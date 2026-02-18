import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.conf import settings
from .models import Project, Material, ShoppingList, ShoppingListItem, UserMaterial
from .serializers import (
    ProjectSerializer, MaterialSerializer, ProjectMaterialSerializer,
    ShoppingListSerializer, ShoppingListCreateSerializer, ShoppingListItemSerializer,
    UserMaterialSerializer, ProductResultSerializer
)
from .store_search import get_store_client


class StoreSearchViewSet(viewsets.ViewSet):
    """ViewSet for searching products across different stores.
    
    Provides a single unified endpoint for searching products,
    hiding store-specific implementation details.
    """
    permission_classes = [IsAuthenticated]
    
    logger = logging.getLogger(__name__)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search for products by query string.
        
        Query Parameters:
            q (required): Search query string
            store (optional): Store name (default: "amazon")
            limit (optional): Max number of results (default: 5)
        
        Returns:
            List of ProductResult objects with normalized product data
        """
        # Get and validate query parameter
        query = request.query_params.get('q')
        if not query:
            return Response(
                {'detail': 'q query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional parameters
        store = request.query_params.get('store', 'amazon').lower()
        try:
            limit = int(request.query_params.get('limit', 5))
        except ValueError:
            limit = 5
        
        # Check if we should use dummy client (for testing)
        use_dummy = getattr(settings, 'STORE_SEARCH_USE_DUMMY', False)
        
        try:
            # Get appropriate store client
            client = get_store_client(store, use_dummy=use_dummy)
            
            # Perform search
            self.logger.info(
                "Store search: user=%s store=%s query=%s limit=%s use_dummy=%s",
                request.user.id,
                store,
                query,
                limit,
                use_dummy
            )
            results = client.search_products(query, limit=limit)
            
            # Serialize results
            serializer = ProductResultSerializer(results, many=True)
            return Response(serializer.data)
            
        except ValueError as e:
            self.logger.warning(f"Invalid store parameter: {store}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except NotImplementedError as e:
            self.logger.warning(f"Store not implemented: {store}")
            return Response(
                {'detail': f"Store '{store}' is not yet supported"},
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        except Exception as e:
            self.logger.exception(f"Error searching store: {store}")
            return Response(
                {'detail': 'Error searching products. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(APIView):
    """Simple token-based login endpoint for Phase 1.

    POST { "username": "...", "password": "..." } -> { "token": "...", "user_id": 1 }
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'detail': 'username and password required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id})



class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing projects and their default materials.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @action(detail=True, methods=['get'])
    def default_materials(self, request, pk=None):
        """Get default materials for a specific project."""
        project = self.get_object()
        materials = project.materials.all()
        serializer = ProjectMaterialSerializer(materials, many=True)
        return Response(serializer.data)


class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving materials.
    """
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer


class ShoppingListViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shopping lists (strict auth)."""
    serializer_class = ShoppingListSerializer
    permission_classes = [IsAuthenticated]

    logger = logging.getLogger(__name__)

    def get_queryset(self):
        """Return shopping lists for the current user."""
        return ShoppingList.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ShoppingListCreateSerializer
        return ShoppingListSerializer

    def perform_create(self, serializer):
        """Create shopping list with the current authenticated user."""
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create with detailed logging to help debug BadRequest issues."""
        try:
            # Record basic context (avoid logging sensitive tokens)
            auth_present = bool(request.META.get('HTTP_AUTHORIZATION'))
            self.logger.info(
                "ShoppingList create requested: user=%s auth_present=%s data=%s",
                getattr(request.user, 'id', None),
                auth_present,
                request.data,
            )

            # Use serializer for validation and detailed errors
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                # Log validation errors and return
                self.logger.warning(
                    "ShoppingList create validation failed: user=%s errors=%s data=%s",
                    getattr(request.user, 'id', None),
                    serializer.errors,
                    request.data,
                )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Save with the authenticated user
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            self.logger.debug(
                "ShoppingList created: user=%s shopping_list_id=%s",
                getattr(request.user, 'id', None),
                serializer.data.get('id')
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except Exception as exc:
            # Log exception with stack trace for diagnostics
            self.logger.exception(
                "Unexpected error creating ShoppingList for user=%s data=%s",
                getattr(request.user, 'id', None),
                request.data,
            )
            return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def user(self, request, *args, **kwargs):
        """Get shopping lists for a specified user (only own or if superuser)."""
        # Log incoming parameters for debugging
        self.logger.info(
            "ShoppingList.user called: requester=%s query_params=%s",
            getattr(request.user, 'id', None),
            dict(request.query_params),
        )

        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'detail': 'user_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user_id = int(user_id)
        except ValueError:
            return Response(
                {'detail': 'user_id must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Only allow users to access their own shopping lists (unless superuser)
        # note: user_id is a string from query params; compare as int
        if int(user_id) != request.user.id and not request.user.is_superuser:
            return Response(
                {'detail': 'You can only view your own shopping lists'},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = ShoppingList.objects.filter(user__id=user_id)
        serializer = self.get_serializer(queryset, many=True)

        # Log brief summary of response (count and ids) and full debug at DEBUG level
        ids = [s.get('id') for s in serializer.data]
        self.logger.info(
            "ShoppingList.user responding: requester=%s user_id=%s count=%s ids=%s",
            getattr(request.user, 'id', None),
            user_id,
            len(ids),
            ids,
        )
        self.logger.debug("ShoppingList.user full response: %s", serializer.data)

        return Response(serializer.data)


class ShoppingListItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shopping list items.
    """
    serializer_class = ShoppingListItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return items from shopping lists owned by the current user."""
        return ShoppingListItem.objects.filter(shopping_list__user=self.request.user)

    def get_serializer_context(self):
        """Pass shopping list to serializer."""
        context = super().get_serializer_context()
        list_id = self.request.parser_context['kwargs'].get('shopping_list_id')
        if list_id:
            context['shopping_list'] = get_object_or_404(
                ShoppingList.objects.filter(user=self.request.user),
                id=list_id
            )
        # Check if material data is provided for auto-creation
        if self.request.data:
            material_data = self.request.data.copy()
            if 'material' not in material_data and 'name' in material_data:
                context['material_data'] = material_data
        return context

    def get_object(self):
        """Resolve object by pk or by material_id when provided in the URL.

        This allows routes like /api/user-materials/<user_id>/<material_id>/ to
        locate the UserMaterial for the authenticated user by material id.
        """
        material_id = self.kwargs.get('material_id')
        if material_id is not None:
            return get_object_or_404(
                UserMaterial.objects.filter(user=self.request.user),
                material__id=material_id,
            )
        return super().get_object()

    def create(self, request, *args, **kwargs):
        """Handle both existing and new materials, with optional product selection.
        
        Accepts optional product_selection dict with fields:
        - name, description, price, currency, sku, url, image_url, store
        
        If product_selection is provided, Material is updated with product details.
        If not provided, Material is created with minimal data.
        """
        shopping_list_id = kwargs.get('shopping_list_id')
        shopping_list = get_object_or_404(
            ShoppingList.objects.filter(user=request.user),
            id=shopping_list_id
        )

        data = request.data.copy()
        quantity = data.pop('quantity', 1)
        product_selection = data.pop('product_selection', None)

        # Check if material_id is provided
        if 'material' in data:
            material_id = data['material']
            material = get_object_or_404(Material, id=material_id)
        else:
            # Auto-create material from provided data
            name = data.get('name')
            category = data.get('category', 'general')  # Default category if not provided
            unit = data.get('unit', 'piece')
            store = data.get('store')

            if not name:
                return Response(
                    {'detail': 'name is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            material, _ = Material.objects.get_or_create(
                name=name,
                category=category,
                unit=unit,
                defaults={'store': store}
            )
            
            # If product_selection provided, update material with product details
            if product_selection:
                material.store = product_selection.get('store', material.store)
                material.sku = product_selection.get('sku', material.sku)
                material.product_title = product_selection.get('name')
                material.product_url = product_selection.get('url')
                material.product_image_url = product_selection.get('image_url')
                material.save()

        # Get or create shopping list item
        item, created = ShoppingListItem.objects.get_or_create(
            shopping_list=shopping_list,
            material=material,
            defaults={'quantity': quantity}
        )

        if not created:
            # Update quantity if item already exists
            item.quantity = quantity
            item.save()

        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserMaterialViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user's material inventory.
    """
    serializer_class = UserMaterialSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'material_id'

    def get_queryset(self):
        """Return materials for current or specified user."""
        user_id = self.kwargs.get('user_id')
        if user_id:
            # Allow users to only see their own materials
            if int(user_id) == self.request.user.id:
                return UserMaterial.objects.filter(user__id=user_id)
            return UserMaterial.objects.none()
        return UserMaterial.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        """Pass user to serializer."""
        context = super().get_serializer_context()
        user_id = self.kwargs.get('user_id')
        if user_id:
            context['user'] = get_object_or_404(
                self.request.user.__class__,
                id=user_id
            )
        else:
            context['user'] = self.request.user
        return context

    def get_object(self):
        """Resolve UserMaterial by material_id using material__id lookup."""
        material_id = self.kwargs.get('material_id')
        if material_id is not None:
            return get_object_or_404(
                UserMaterial.objects.filter(user=self.request.user),
                material__id=material_id,
            )
        return super().get_object()

    def create(self, request, *args, **kwargs):
        """Handle creation of user material."""
        user_id = kwargs.get('user_id')
        if not user_id or int(user_id) != request.user.id:
            return Response(
                {'detail': 'You can only manage your own materials'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()

        # Check if material_id is provided
        if 'material' in data:
            material_id = data['material']
            material = get_object_or_404(Material, id=material_id)
        else:
            # Auto-create material from provided data
            name = data.get('name')
            category = data.get('category')
            unit = data.get('unit', 'piece')
            store = data.get('store')

            if not name or not category:
                return Response(
                    {'detail': 'name and category are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            material, _ = Material.objects.get_or_create(
                name=name,
                category=category,
                unit=unit,
                defaults={'store': store}
            )

        quantity = data.get('quantity', 1)

        # Get or create user material
        user_material, created = UserMaterial.objects.get_or_create(
            user=request.user,
            material=material,
            defaults={'quantity': quantity}
        )

        serializer = self.get_serializer(user_material)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


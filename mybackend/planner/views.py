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
from .models import Project, Material, ShoppingList, ShoppingListItem, UserMaterial
from .serializers import (
    ProjectSerializer, MaterialSerializer, ProjectMaterialSerializer,
    ShoppingListSerializer, ShoppingListCreateSerializer, ShoppingListItemSerializer,
    UserMaterialSerializer
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

    def create(self, request, *args, **kwargs):
        """Handle both existing and new materials."""
        shopping_list_id = kwargs.get('shopping_list_id')
        shopping_list = get_object_or_404(
            ShoppingList.objects.filter(user=request.user),
            id=shopping_list_id
        )

        data = request.data.copy()
        quantity = data.pop('quantity', 1)

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

        # Get or create shopping list item
        item, created = ShoppingListItem.objects.get_or_create(
            shopping_list=shopping_list,
            material=material,
            defaults={'quantity': quantity}
        )

        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserMaterialViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user's material inventory.
    """
    serializer_class = UserMaterialSerializer
    permission_classes = [IsAuthenticated]

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


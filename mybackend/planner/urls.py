from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, MaterialViewSet, ShoppingListViewSet,
    ShoppingListItemViewSet, UserMaterialViewSet, StoreSearchViewSet, LoginView,
    PlanGenerationView
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'materials', MaterialViewSet, basename='material')
router.register(r'shopping-lists', ShoppingListViewSet, basename='shopping-list')
router.register(r'store-search', StoreSearchViewSet, basename='store-search')

# Shopping list items - nested router
shopping_list_items_router = DefaultRouter()
shopping_list_items_router.register(
    r'items',
    ShoppingListItemViewSet,
    basename='shopping-list-item'
)

# User materials - nested router
user_materials_router = DefaultRouter()
user_materials_router.register(
    r'',
    UserMaterialViewSet,
    basename='user-material'
)

urlpatterns = [
    # Main routes
    path('', include(router.urls)),

    # Nested shopping list items
    path('shopping-lists/<int:shopping_list_id>/', include(shopping_list_items_router.urls)),

    # Shopping list items detail (flat route for PATCH/DELETE)
    path('shopping-list-items/<int:pk>/', ShoppingListItemViewSet.as_view({
        'patch': 'partial_update',
        'delete': 'destroy',
        'get': 'retrieve'
    }), name='shopping-list-item-detail'),

    # User material update (flat route for PATCH/DELETE) - MUST be before the nested router
    path('user-materials/<int:user_id>/<int:material_id>/', UserMaterialViewSet.as_view({
        'patch': 'partial_update',
        'delete': 'destroy',
    }), name='user-material-update'),

    # User materials (nested router - comes after specific flat route)
    path('user-materials/<int:user_id>/', include(user_materials_router.urls)),
    # Simple auth
    path('auth/login/', LoginView.as_view(), name='api-login'),
    # Phase 3: Plan generation endpoint
    path('generate-plan/', PlanGenerationView.as_view(), name='generate-plan'),
]

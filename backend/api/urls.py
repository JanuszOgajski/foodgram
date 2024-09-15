from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet
from users.views import LoginView, LogoutView, UserViewSet

router_v1 = DefaultRouter()
router_v1.register(
    'users', UserViewSet, basename='users'
)
router_v1.register(
    'recipes', RecipeViewSet, basename='recipes'
)
router_v1.register(
    'ingredients', IngredientViewSet, basename='ingredients'
)
router_v1.register(
    'tags', TagViewSet, basename='tags'
)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/token/login/', LoginView.as_view(), name='login'),
    path('auth/token/logout/', LogoutView.as_view(), name='logout'),
    path('', include('djoser.urls')),
]

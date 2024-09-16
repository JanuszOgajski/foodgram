from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingCart, Tag)
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPagination
from .permissions import IsAdminOrAuthor
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeReceiveSerializer,
                          ShoppingCartSerializer, TagSerializer)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all().select_related(
        'author'
    ).prefetch_related(
        'tags', 'ingredients_in_recipe__ingredient'
    )
    permission_classes = (IsAdminOrAuthor, IsAuthenticatedOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitPagination
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeReceiveSerializer
        return RecipeCreateSerializer

    @action(
        methods=('GET',),
        detail=True,
        url_path='get-link',
    )
    def get_short_link(self, request, pk):
        """Генерация короткой ссылки на рецепт."""
        get_object_or_404(Recipe, id=pk)
        link = request.build_absolute_uri(f'/recipes/{pk}/')
        return Response({'short-link': link}, status=status.HTTP_200_OK)

    @action(
        methods=('POST',),
        permission_classes=(IsAuthenticated,),
        detail=True
    )
    def shopping_cart(self, request, pk):
        """Добавление рецепта в список покупок."""
        return self.add_recipe(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk):
        """Удаление рецепта из списка покупок."""
        return self.delete_recipe(request, pk, ShoppingCart)

    @action(
        methods=('POST',),
        permission_classes=(IsAuthenticated,),
        detail=True,
    )
    def favorite(self, request, pk):
        """Добавление рецепта в избранное."""
        return self.add_recipe(request, pk, FavoriteSerializer)

    @favorite.mapping.delete
    def delete_from_favorite(self, request, pk):
        """Удаление рецепта из избранного."""
        return self.delete_recipe(request, pk, Favorite)

    @action(
        methods=('GET',),
        permission_classes=(IsAuthenticated,),
        detail=False
    )
    def download_shopping_cart(self, request):
        """Загрузка списка покупок файлом."""
        user = request.user
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shoppingcarts__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list = "Shopping List:\n\n"
        for item in ingredients:
            shopping_list += (
                f"{item['ingredient__name']}: "
                f"{item['total_amount']} "
                f"{item['ingredient__measurement_unit']}\n"
            )
        response = HttpResponse(shopping_list, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'
        return response

    def add_recipe(self, request, pk, serializer_class):
        """Добавление рецепта в избранное или в список покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)

        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = serializer_class(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, request, pk, model):
        """Удаление рецепта из избранного или списка покупок."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        recipe_in_cart = user.shoppingcarts.filter(recipe=recipe)
        if model == Favorite:
            recipe_in_cart = user.favorites.filter(recipe=recipe)
        if recipe_in_cart.exists():
            recipe_in_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'errors': 'Рецепт не найден в списке.'},
            status=status.HTTP_400_BAD_REQUEST
        )

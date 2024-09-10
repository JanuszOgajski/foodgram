# flake8:noqa
from django_filters.rest_framework import filters, FilterSet
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientFilter(SearchFilter):
    """Фильтрация для ингредиентов."""

    search_param = 'name'


class RecipeFilter(FilterSet):
    """Фильтрация для рецептов."""

    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='is_in_shopping_cart_filter'
    )
    is_favorited = filters.NumberFilter(
        method='is_favorited_filter'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def is_in_shopping_cart_filter(self, queryset, name, value):
        """Фильтрация для рецептов в списке покупок."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(shoppingcarts__user=self.request.user)
        return queryset

    def is_favorited_filter(self, queryset, name, value):
        """Фильтрация для рецептов в избранном."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

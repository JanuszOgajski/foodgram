from django.contrib import admin
from django.utils.safestring import mark_safe

from .constants import EXTRA, MIN_NUM
from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)

admin.site.empty_value_display = 'Здесь пока ничего нет:('


class IngredientInRecipeInline(admin.TabularInline):
    """Связанная админ панель для ингредиентов в рецепте."""

    model = IngredientInRecipe
    extra = EXTRA
    min_num = MIN_NUM


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ панель для ингредиентов."""

    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'name',
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ панель для тегов."""

    list_display = (
        'name',
        'slug',
    )
    search_fields = (
        'name',
        'slug',
    )
    list_filter = (
        'name',
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """"Админ панель для рецептов."""

    list_display = (
        'author',
        'name',
        'recipe_favorite_additions',
        'recipe_ingredients',
        'recipe_tags',
        'recipe_image',
    )
    list_editable = (
        'name',
    )
    search_fields = (
        'author__username',
        'name',
    )
    list_filter = (
        'tags',
    )
    inlines = (IngredientInRecipeInline,)

    @admin.display(description='Добавлений в избранное')
    def recipe_favorite_additions(self, recipe):
        """Считает кол-во добавлений рецепта в избранное."""
        return recipe.favorites.all().count()

    @admin.display(description='Ингредиенты')
    def recipe_ingredients(self, recipe):
        """Возвращает ингредиенты через запятую."""
        return ', '.join(
            ingredient.name for ingredient in recipe.ingredients.all()
        )

    @admin.display(description='Теги')
    def recipe_tags(self, recipe):
        """Возвращает теги через запятую."""
        return ', '.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Изображение')
    def recipe_image(self, recipe):
        """Отображает изображение рецепта в админке."""
        return mark_safe(
            f'<img src="{recipe.image.url}" width="80" height="60">'
        )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """"Админ панель для рецептов."""

    list_display = (
        'user',
        'recipe',
    )
    search_fields = (
        'user',
    )
    list_filter = (
        'user',
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ панель для избранного."""

    list_display = (
        'user',
        'recipe',
    )
    search_fields = (
        'user',
    )
    list_filter = (
        'user',
    )

import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.constants import (MAX_COOKING_TIME, MAX_INGREDIENTS_AMOUNT,
                               MIN_COOKING_TIME, MIN_INGREDIENTS_AMOUNT)
from recipes.models import (Favorite, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingCart, Tag)
from users.serializers import RecipeShortSerializer, UserSerializer


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class AddIngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENTS_AMOUNT,
        max_value=MAX_INGREDIENTS_AMOUNT,
        error_messages={
            'min_value': 'Кол-во ингредиента не может быть меньше '
            f'{MIN_INGREDIENTS_AMOUNT}.',
            'max_value': 'Кол-во ингредиента не может быть больше '
            f'{MAX_INGREDIENTS_AMOUNT}.',
            'invalid': 'Укажите корректное кол-во ингредиента.',
        }
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeReceiveSerializer(serializers.ModelSerializer):
    """Сериализатор для получения рецепта."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='ingredients_in_recipe',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context['request']
        return (
            request.user.is_authenticated
            and obj.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        return (
            request.user.is_authenticated
            and obj.shoppingcarts.filter(user=request.user).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""

    ingredients = AddIngredientInRecipeSerializer(
        many=True,
        allow_empty=False,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False,
    )
    image = Base64ImageField(
        allow_null=False,
        allow_empty_file=False,
    )
    cooking_time = serializers.IntegerField(
        max_value=MAX_COOKING_TIME,
        min_value=MIN_COOKING_TIME,
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def to_representation(self, instance):
        return RecipeReceiveSerializer(instance, context=self.context).data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        self.add_ingredient(ingredients=ingredients, recipe=recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])

        instance.ingredients.clear()
        self.add_ingredient(ingredients=ingredients, recipe=instance)
        instance.tags.set(tags)

        return super().update(instance, validated_data)

    def add_ingredient(self, ingredients, recipe):
        IngredientInRecipe.objects.bulk_create(
            [
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'],
                )
                for ingredient in ingredients
            ],
            ignore_conflicts=True
        )

    def validate(self, data):
        ingredients = data.get('ingredients', [])

        ingredients_ids = [ingredient['id'] for ingredient in ingredients]
        tags_ids = self.initial_data.get('tags')

        if not tags_ids or not ingredients:
            raise serializers.ValidationError({'Недостаточно данных.'})

        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты должны быть уникальными.'
            })

        if len(tags_ids) != len(set(tags_ids)):
            raise serializers.ValidationError({
                'tags': 'Теги должны быть уникальными.'
            })

        return data


class ShoppingCartFavoriteSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранного и списка покупок."""

    class Meta:
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context=self.context
        ).data

    def validate_recipe(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепта не существует.'
            )
        return value


class ShoppingCartSerializer(ShoppingCartFavoriteSerializer):
    """Сериализатор для списка покупок."""

    validators = [
        UniqueTogetherValidator(
            queryset=ShoppingCart.objects.all(),
            fields=('user', 'recipe'),
            message='Список с пользователем и рецептом уже существует'
        )
    ]

    class Meta(ShoppingCartFavoriteSerializer.Meta):
        model = ShoppingCart


class FavoriteSerializer(ShoppingCartFavoriteSerializer):
    """Сериализатор для избранного."""
    validators = [
        UniqueTogetherValidator(
            queryset=Favorite.objects.all(),
            fields=('user', 'recipe'),
            message='Список с пользователем и рецептом уже существует'
        )
    ]

    class Meta(ShoppingCartFavoriteSerializer.Meta):
        model = Favorite

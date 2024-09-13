# flake8:noqa
import base64

from django.core.files.base import ContentFile
from django.db import IntegrityError
# from django.db import transaction
# from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.constants import MAX_INGREDIENTS_AMOUNT, MIN_INGREDIENTS_AMOUNT
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserCreateSerializer(serializers.ModelSerializer):  # DjoserUserSerializer
    """Сериализатор для пользователя."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'password',
            'first_name',
            'last_name',
            'username'
        )
        extra_kwargs = {'password': {'write_only': True}}

    """def validate(self, data):
        try:
            User.objects.get_or_create(
                username=data.get('username'),
                email=data.get('email')
            )
        except IntegrityError:
            raise serializers.ValidationError(
                'Такой пользователь уже существует'
            )
        return data"""

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):  # DjoserUserSerializer
    """Сериализатор для пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    # avatar = Base64ImageField()

    class Meta:  # (DjoserUserSerializer.Meta)
        # fields = DjoserUserSerializer.Meta.fields + (
        #     'is_subscribed',
        #     'avatar'
        # )
        # ref_name = 'UniqueUserSerializer'
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
            # 'password',
        )
        read_only_fields = ('id', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and Subscription.objects.filter(user=user, author=obj).exists()
            # and User.subscribed_to.all().exists()
        )


class UserAvatarSerializer(UserSerializer):
    """Сериализатор для работы с аватаром пользователя."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if 'avatar' not in data:
            raise serializers.ValidationError(
                {'avatar': 'This field is required.'}
            )
        return data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Информации о рецепте в корзине и избранном."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionReceiveSerializer(UserSerializer):
    """Сериализатор для получения подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        read_only=True,
        default=0
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        """Получить список рецептов."""
        recipes = obj.recipes.all()
        request = self.context.get('request')
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                try:
                    recipes = recipes[:int(recipes_limit)]
                except (ValueError, TypeError):
                    pass

        return RecipeShortSerializer(
            recipes, context=self.context, many=True
        ).data


class SubscribeToSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки или отписки."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def to_representation(self, instance):
        return SubscriptionReceiveSerializer(
            instance.author, context=self.context
        ).data

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя'
            )
        return data

from io import BytesIO

from django.db.models import Count, Sum
from django.http import HttpResponse  # FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
# from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User
from .download_shopping_cart import download_txt
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPagination
from .permissions import IsAdminOrAuthor
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeReceiveSerializer,
                          ShoppingCartSerializer, SubscribeToSerializer,
                          SubscriptionReceiveSerializer, TagSerializer,
                          UserAvatarSerializer, UserSerializer)


class UserViewSet(viewsets.ModelViewSet):  # (DjoserUserViewSet)
    """Вьюсет для юзера."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    @action(
        methods=('GET',),
        permission_classes=(IsAuthenticated,),
        detail=False
    )
    def me(self, request):
        """Возвращает информацию о профиле текущего пользователя."""
        serializer = UserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=('PUT',),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
        detail=False
    )
    def update_avatar(self, request):
        """Обновляет аватар пользователя."""
        user = self.request.user

        serializer = UserAvatarSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар пользователя."""
        user = request.user

        if user.avatar:
            user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        pagination_class=LimitPagination,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Возвращает все подписки пользователя."""
        # queryset = User.objects.filter(
        #     subscribed_to__user=request.user
        # ).annotate(recipes_count=Count('recipes')).order_by('username')
        queryset = User.subscribed_to.all(
        ).annotate(recipes_count=Count('recipes')).order_by('username')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionReceiveSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionReceiveSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,),
        pagination_class=LimitPagination,
        url_path='subscribe',
    )
    def subscribe_to(self, request, id):
        """Подписка на пользователя."""
        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {'author': author.id, 'user': user.id}
        serializer = SubscribeToSerializer(
            data=data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @subscribe_to.mapping.delete
    def unsubscribe(self, request, id):
        """Отписаться от пользователя."""
        user = request.user
        author = get_object_or_404(User, pk=id)
        # deleted_count, _ = Subscription.objects.filter(
        #     user=user, author=author
        # ).delete()
        deleted_count, _ = author.subscribed_to.all().delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
            if deleted_count else status.HTTP_400_BAD_REQUEST,
            data={'errors': 'Подписка не найдена.'}
        )


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

        # content = download_txt(ingredients, user=user.username)

        # file_content = BytesIO(content.encode('utf-8'))

        # response = FileResponse(
        #     file_content,
        #     content_type='text/plain; charset=utf-8'
        # )
        # response['Content-Disposition'] = (
        #     f'attachment; filename="shopping_cart_{user.username}.txt"'
        # )

        # return response

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

        deleted_count, _ = model.objects.filter(
            recipe_id=pk, user=user
        ).delete()

        if deleted_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не найден в списке.'},
            status=status.HTTP_400_BAD_REQUEST
        )

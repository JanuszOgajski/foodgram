# flake8:noqa
from django.contrib.auth import authenticate, update_session_auth_hash
from django.db.models import Count
from django.shortcuts import get_object_or_404
# from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.pagination import LimitPagination
from users.models import User, Subscription
from users.serializers import (SubscribeToSerializer,
                               SubscriptionReceiveSerializer,
                               UserAvatarSerializer, UserCreateSerializer,
                               UserSerializer)


class LoginView(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'auth_token': token.key,
        })


class LogoutView(ObtainAuthToken):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        token = get_object_or_404(Token, user=user)
        token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):  # (DjoserUserViewSet)
    """Вьюсет для юзера."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    def get_permissions(self):
        permission_classes = []
        if self.action in ['list', 'retrieve', 'create']:
            permission_classes = [AllowAny]
        elif self.action in [
            'subscribe',
            'unsubscribe',
            'subscriptions',
            'reset_password',
            'me',
            'update_avatar',
            'delete_avatar'
        ]:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

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
        queryset = User.objects.filter(
            subscribed_to__user=request.user
        ).annotate(recipes_count=Count('recipes')).order_by('username')
        # queryset = User.subscribed_to.all(
        # ).annotate(recipes_count=Count('recipes')).order_by('username')

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
    def subscribe(self, request, pk):
        """Подписка на пользователя."""
        user = request.user
        author = get_object_or_404(User, pk=pk)
        data = {'author': author.id, 'user': user.id}
        serializer = SubscribeToSerializer(
            data=data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk):
        """Отписаться от пользователя."""
        user = request.user
        author = get_object_or_404(User, pk=pk)
        # deleted_count, _ = Subscription.objects.filter(
        #     user=user, author=author
        # ).delete()
        # # deleted_count, _ = author.subscribed_to.all().delete()
        """deleted_count, _ = author.subscribed_to.all().delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
            if deleted_count else status.HTTP_400_BAD_REQUEST,
            data={'errors': 'Подписка не найдена.'}
        )"""
        follow = Subscription.objects.filter(
            user=user,
            author=author
        ).first()  # .first()
        if follow:
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Подписка не найдена.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['post'], url_path='set_password')
    def reset_password(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not user.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)

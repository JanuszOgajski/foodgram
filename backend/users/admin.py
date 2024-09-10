from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscription, User

admin.site.empty_value_display = 'Здесь пока ничего нет:('


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админ панель для пользователя."""

    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'recipes_count',
        'subscribers_count',
    )
    list_editable = (
        'first_name',
        'last_name',
    )
    search_fields = (
        'email',
        'username',
    )
    list_filter = (
        'email',
        'username',
    )

    @admin.display(description='Рецепты')
    def recipes_count(self, obj):
        """Считает кол-во рецептов пользователя."""
        return obj.recipes.count()

    @admin.display(description='Подписчики')
    def subscribers_count(self, obj):
        """Считает кол-во подписчиков пользователя."""
        return obj.subscribed_to.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ панель для подписки."""

    list_display = (
        'user',
        'author',
    )
    search_fields = (
        'user',
        'author',
    )
    list_filter = (
        'user',
        'author',
    )

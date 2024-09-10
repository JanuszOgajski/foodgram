from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.forms import ValidationError

from .constants import (CHAR_LIMIT, MAX_EMAIL_LEN, MAX_FIRST_NAME_LEN,
                        MAX_LAST_NAME_LEN, MAX_USERNAME_LEN)
from .validators import validate_username


class User(AbstractUser):
    """Кастомная модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField(
        unique=True,
        max_length=MAX_EMAIL_LEN,
        verbose_name='Email',
    )
    username = models.CharField(
        unique=True,
        max_length=MAX_USERNAME_LEN,
        validators=(validate_username,),
        verbose_name='Имя пользователя',
    )
    first_name = models.CharField(
        max_length=MAX_FIRST_NAME_LEN,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=MAX_LAST_NAME_LEN,
        verbose_name='Фамилия',
    )
    avatar = models.ImageField(
        upload_to='users/images/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=('png', 'jpg', 'jpeg'))
        ],
        verbose_name='Изображение аватара',
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username[:CHAR_LIMIT]


class Subscription(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed_to',
        verbose_name='Автор',
    )

    def clean(self):
        if self.user == self.author:
            raise ValidationError(
                'Вы не можете подписаться на самого себя.'
            )

    class Meta:
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author',
            )
        ),
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return (
            f'{self.user.username} подписан на {self.author.username}'
        )

from django.core.validators import (FileExtensionValidator, MaxValueValidator,
                                    MinValueValidator)
from django.db import models

from users.models import User
from .constants import (CHAR_LIMIT, MAX_COOKING_TIME, MAX_INGREDIENT_NAME_LEN,
                        MAX_INGREDIENTS_AMOUNT, MAX_RECIPE_NAME_LEN,
                        MAX_TAG_NAME_LEN, MAX_TAG_SLUG_LEN,
                        MEASUREMENT_UNIT_CHOICES, MIN_COOKING_TIME,
                        MIN_INGREDIENTS_AMOUNT)


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        unique=True,
        max_length=MAX_INGREDIENT_NAME_LEN,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        # max(len(choice) for choice, _ in MEASUREMENT_UNIT_CHOICES),
        max_length=25,
        choices=MEASUREMENT_UNIT_CHOICES,
        verbose_name='Единица измерения',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit',
            ),
        )
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name[:CHAR_LIMIT]


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        unique=True,
        max_length=MAX_TAG_NAME_LEN,
        verbose_name='Название',
    )
    slug = models.SlugField(
        unique=True,
        max_length=MAX_TAG_SLUG_LEN,
        verbose_name='Слаг',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:CHAR_LIMIT]


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LEN,
        verbose_name='Название',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        validators=(
            FileExtensionValidator(allowed_extensions=('png', 'jpg', 'jpeg')),
        ),
        verbose_name='Картинка',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        db_index=True,
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                MIN_COOKING_TIME,
                message=(
                    'Время приготовления не может быть меньше '
                    f'{MIN_COOKING_TIME} минут(ы)!'
                )
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message=(
                    'Время приготовления не может быть больше '
                    f'{MAX_COOKING_TIME} минут!'
                )
            )
        ),
        db_index=True,
        verbose_name='Время приготовления в минутах',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:CHAR_LIMIT]


class IngredientInRecipe(models.Model):
    """Модель ингредиента в рецепте."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipe',
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipe',
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                MIN_INGREDIENTS_AMOUNT,
                message=(
                    'Кол-во ингредиентов не может быть '
                    f'меньше {MIN_INGREDIENTS_AMOUNT}!'
                )
            ),
            MaxValueValidator(
                MAX_INGREDIENTS_AMOUNT,
                message=(
                    'Кол-во ингредиентов не может быть '
                    f'больше {MAX_INGREDIENTS_AMOUNT}!'
                )
            )
        ),
        verbose_name='Кол-во',
    )

    class Meta:
        ordering = ('ingredient',)
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        )
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        return (
            f'{self.recipe.name} {self.ingredient.name}'
        )


class UserRecipeModel(models.Model):
    """Абстрактная модель для связи пользователя и рецепта."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_%(class)s',
            ),
        )
        ordering = ('id', 'user__username')

    def __str__(self):
        return (
            f'{self.user.username} добавил {self.recipe.name} '
            f'в {self._meta.verbose_name}'
        )


class ShoppingCart(UserRecipeModel):
    """Модель списка покупок."""

    class Meta(UserRecipeModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class Favorite(UserRecipeModel):
    """Модель избранного."""

    class Meta(UserRecipeModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

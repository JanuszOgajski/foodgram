# Ограничение на вывод символов:
CHAR_LIMIT = 20

# Ограничение на длину названия рецепта:
MAX_RECIPE_NAME_LEN = 128

# Минимальное время приготовления:
MIN_COOKING_TIME = 1

# Максимальное время приготовления:
MAX_COOKING_TIME = 32000

# Ограничение на длину названия тега:
MAX_TAG_NAME_LEN = 64

# Ограничение на длину слага тега:
MAX_TAG_SLUG_LEN = 128

# Ограничение на длину названия ингредиента:
MAX_INGREDIENT_NAME_LEN = 128

# Минимальное кол-во ингредиентов:
MIN_INGREDIENTS_AMOUNT = 1

# Максимальное кол-во ингредиентов:
MAX_INGREDIENTS_AMOUNT = 32000

# Кол-во дополнительных пустых строк в админке:
EXTRA = 0

# Минимальное количество строк:
MIN_NUM = 1

# Единицы измерения ингредиентов
GRAMS = 'г'
KILOGRAMS = 'кг'
MILLILITERS = 'мл'
LITERS = 'L'
SPOONFULLS = 'ст. л.'
TEASPOONS = 'ч. л.'
PIECES = 'шт.'
CHUNK = 'кусок'
DROP = 'капля'
MEASUREMENT_UNIT_CHOICES = (
    (GRAMS, GRAMS),
    (KILOGRAMS, KILOGRAMS),
    (MILLILITERS, MILLILITERS),
    (LITERS, LITERS),
    (SPOONFULLS, SPOONFULLS),
    (TEASPOONS, TEASPOONS),
    (CHUNK, CHUNK),
    (DROP, DROP),
    (PIECES, PIECES),
)

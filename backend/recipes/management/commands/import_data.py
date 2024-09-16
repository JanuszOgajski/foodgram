# flake8:noqa
import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag

# Путь до директории с json-файлами
JSON_PATH = os.path.join(
    Path(__file__).resolve().parent.parent.parent.parent, 'data')

# Словарь соответствий модели и json-файла
MODEL_FILE_MATCHING = {
    Tag: 'tags.json',
    Ingredient: 'ingredients.json',
}


class Command(BaseCommand):
    """Пользовательская команда Django для импорта данных из json в БД."""

    help = 'Загружает данные из файлов json в БД'

    def handle(self, *args, **kwargs):
        for model, file_name in MODEL_FILE_MATCHING.items():
            file_path = os.path.join(JSON_PATH, file_name)
            error_occurred = False
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    objects_to_create = [model(**item) for item in data]

                    model.objects.bulk_create(
                        objects_to_create, ignore_conflicts=True
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            'SUCCESSFULLY LOADED '
                            f'`{model.__name__.upper()}` DATA'
                        )
                    )
            except Exception as error:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing file {file_path}: {error}'
                    )
                )
                error_occurred = True

            if error_occurred:
                self.stdout.write(
                    self.style.ERROR(
                        f'FAILED TO LOAD `{model.__name__.upper()}` DATA'
                    )
                )

from datetime import date


def download_txt(data, user):
    """Функция для загрузки списка покупок в txt формате."""

    current_date = date.today().strftime('%d-%m-%Y')
    header = f'Список покупок {user}\nДата: {current_date}'

    file_data = '\n'.join([
        f'{item["ingredient__name"]} {item["total_amount"]} '
        f'{item["ingredient__measurement_unit"]}'
        for item in data
    ])

    content = f'{header}\n\n{file_data}'

    return content

from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    """Класс пагинации с обновленным полем кол-ва результатов."""

    page_size = 6
    page_size_query_param = 'limit'

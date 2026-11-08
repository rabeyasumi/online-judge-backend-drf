from rest_framework.pagination import PageNumberPagination


class ProblemPagination(PageNumberPagination):
    page_size = 8
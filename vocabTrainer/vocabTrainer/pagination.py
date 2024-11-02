from rest_framework.pagination import PageNumberPagination

class DefaultPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def __init__(self):
        self.page = None
        self.queryset = None
        self.request = None

    def paginate_queryset(self, queryset, request, view=None):
        page_number = request.query_params.get(self.page_query_param, 0)

        try:
            page_number = int(page_number)
        except (ValueError, TypeError):
            page_number = 0

        if page_number < 0:
            page_number = 0

        self.request = request
        self.queryset = queryset
        self.page_size = self.get_page_size(request)

        if self.page_size is not None:
            self.page = self.django_paginator_class(queryset, self.page_size).page(page_number + 1)
            return self.page.object_list

        return None

from common.paginator import DRFCursorPagination


class TransactionPagination(DRFCursorPagination):
    page_size = 100
    max_page_size = 1000
    page_size_query_param = 'page_size'
    ordering = '-created_at'

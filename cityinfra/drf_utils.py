from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.pagination import LimitOffsetPagination


class MaxLimitOffsetPagination(LimitOffsetPagination):
    max_limit = settings.CITYINFRA_MAXIMUM_RESULTS_PER_PAGE
    limit_query_description = _(f"Number of results to return per page. Maximum number of results is {max_limit}.")

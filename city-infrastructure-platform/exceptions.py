from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def cityinfra_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        if isinstance(exc, IntegrityError):
            message = str(exc)
            if "duplicate key value violates unique constraint" in message and "unique_source_name_id" in message:
                response = Response(
                    data={"detail": "The fields source_name, source_id must make a unique set."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    return response

def requires_annotation(callback):
    """
    Decorator that flags a method as requiring an annotation.
    Stores a reference to the callback function that applies the annotation.
    """

    def decorator(func):
        func.annotation_callback = callback
        return func

    return decorator


def requires_fields(*fields):
    """
    Decorator to annotate admin or model methods with the database fields they require.
    Allows suggest_queryset_optimizations to recursively introspect callables and prevent N+1 queries.
    """

    def decorator(func):
        func.required_fields = fields
        return func

    return decorator

def requires_fields(*fields):
    """Decorator for callable"""

    def decorator(func):
        func.required_fields = fields
        return func

    return decorator


def annotate_queryset(transform_method, annotation_field=None):
    """
    Tags a method to indicate it requires a specific queryset transformation.

    :param transform_method: The name of the @staticmethod on the Model to call.
    :param annotation_field: (Optional) The name of the field that will be added
                             by the annotation. Useful for documentation or future
                             introspection, though the script primarily needs
                             transform_method.
    """

    def decorator(func):
        if not hasattr(func, "queryset_transforms"):
            func.queryset_transforms = set()
        func.queryset_transforms.add(transform_method)
        return func

    return decorator

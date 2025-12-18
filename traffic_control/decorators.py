def requires_fields(*fields):
    """
    Decorates a method (on a Model or Admin class) to declare which database fields
    it accesses. This allows the `admin_assist_get_queryset` management command
    to automatically optimize the queryset by adding these fields to `.only()`
    (projection) and `.select_related()` (joins).

    Usage:
        - Apply to methods used in `list_display`.
        - Apply to `__str__` methods on models to handle recursive dependencies.
        - Use double-underscores (__) to traverse relationships.

    Example:
        class MyAdmin(admin.ModelAdmin):
            list_display = ['user_info']

            @requires_fields("user__first_name", "user__last_name", "created_at")
            def user_info(self, obj):
                # The script will now ensure 'user' is joined and fields are fetched.
                return f"{obj.user.first_name} {obj.user.last_name} ({obj.created_at})"
    """

    def decorator(func):
        func.required_fields = fields
        return func

    return decorator


def annotate_queryset(transform_method, annotation_field=None):
    """
    Decorates a method to indicate that it relies on a specific queryset transformation
    (such as an `.annotate()` or complex `.filter()`) to function correctly.

    The `admin_assist_get_queryset` command uses this to insert the specified
    transformation method into the generated `get_queryset` pipeline.

    :param transform_method: The name of the method (string) on the Admin class
                             (or Model class) that accepts a queryset, applies the
                             transform, and returns the modified queryset.
    :param annotation_field: (Optional) The name of the virtual field added by the
                             annotation. Useful for documentation.

    Example:
        class MyAdmin(admin.ModelAdmin):
            list_display = ['has_large_orders']

            # 1. The method that calculates the data (using the annotation)
            @annotate_queryset("annotate_order_stats", "_has_large")
            def has_large_orders(self, obj):
                return getattr(obj, '_has_large', False)

            # 2. The transformation method that prepares the queryset
            def annotate_order_stats(self, qs):
                return qs.annotate(_has_large=Exists(
                    Order.objects.filter(user=OuterRef('pk'), total__gt=1000)
                ))
    """

    def decorator(func):
        if not hasattr(func, "queryset_transforms"):
            func.queryset_transforms = set()
        func.queryset_transforms.add(transform_method)
        return func

    return decorator

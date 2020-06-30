class Point3DFieldAdminMixin:
    """A mixin class that shows a map for 3d geometries.

    Django's default behaviour is to use a text field for 3d geometries.
    The class must be used together with traffic_control.forms.Point3DFieldForm
    in order to save 3d geometry to model instances
    """

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "location":
            kwargs["widget"] = self.get_map_widget(db_field)
            return db_field.formfield(**kwargs)

        return super().formfield_for_dbfield(db_field, request, **kwargs)


class UserStampedAdminMixin:
    """A mixin class for model admin that set created_by/updated_by from request user"""

    def save_model(self, request, obj, form, change):
        if obj._state.adding:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class UserStampedInlineAdminMixin:
    """
    A mixin class for model admin that sets inline model created_by/updated_by
    from request user
    """

    def save_formset(self, request, form, formset, change):
        objects = formset.save(commit=False)

        for obj in objects:
            if not obj.created_by_id:
                obj.created_by = request.user

            obj.updated_by = request.user
            obj.save()


class SoftDeleteAdminMixin:
    exclude = ("is_active", "deleted_at", "deleted_by")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.active()

    def delete_model(self, request, obj):
        obj.soft_delete(request.user)

    def delete_queryset(self, request, queryset):
        # audit log entries are created via saving signals,
        # using bulk operations will not trigger the signals
        # and will skip the auditing. Thus soft delete
        # objects in queryset one by one.
        for obj in queryset:
            obj.soft_delete(request.user)

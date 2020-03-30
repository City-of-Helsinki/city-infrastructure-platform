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

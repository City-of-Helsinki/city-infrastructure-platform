from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _


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


class EnumChoiceValueDisplayAdminMixin:
    """
    A mixin class for model admin that displays Enum's logical value in the
    option label after the label defined in Enum class.
    """

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        from enumfields import EnumField, EnumIntegerField

        from ..forms import AdminEnumChoiceField

        if isinstance(db_field, (EnumField, EnumIntegerField)):
            return db_field.formfield(choices_form_class=AdminEnumChoiceField, **kwargs)

        return super().formfield_for_choice_field(db_field, request, **kwargs)


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


class SoftDeleteFilter(SimpleListFilter):
    """
    Admin filter that by default excludes soft deleted instances out
    of the list view.
    """

    title = _("Marked as deleted (hidden from API)")
    parameter_name = "soft_deleted"

    def lookups(self, request, model_admin):
        return (
            (None, _("No")),
            ("1", _("Yes")),
        )

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}, []
                ),
                "display": title,
            }

    def queryset(self, request, queryset):
        value = self.value()
        is_active = True

        if value and value == "1":
            is_active = False

        return queryset.filter(is_active=is_active)


class SoftDeleteAdminMixin:
    """
    A mixin class for models that support soft deletion.
    """

    exclude = ("is_active", "deleted_at", "deleted_by")
    actions = ["action_soft_delete", "action_undo_soft_delete"]
    list_filter = [
        SoftDeleteFilter,
    ]

    def action_soft_delete(self, request, queryset):
        queryset.soft_delete(request.user)

    action_soft_delete.short_description = _("Mark selected objects as deleted")
    action_soft_delete.allowed_permissions = ("change", "delete")

    def action_undo_soft_delete(self, request, queryset):
        queryset.update(is_active=True, deleted_by=None, deleted_at=None)

    action_undo_soft_delete.short_description = _(
        "Mark selected objects as not deleted"
    )
    action_undo_soft_delete.allowed_permissions = ("change",)

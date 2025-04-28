from django.contrib.admin import SimpleListFilter
from django.contrib.gis.forms import OSMWidget
from django.utils.translation import gettext_lazy as _

from traffic_control.models.plan import Plan


class CityInfra3DOSMWidget(OSMWidget):
    """This point is near Helsinki railway station"""

    default_lon = 24.9416259
    default_lat = 60.170255
    default_zoom = 12.5
    supports_3d = True


class Geometry3DFieldAdminMixin:
    """A mixin class that shows a map for 3d geometries.

    Django's default behaviour is to use a text field for 3d geometries.
    The class must be used together with traffic_control.forms.Point3DFieldForm
    in order to save 3d geometry to model instances
    """

    gis_widget = CityInfra3DOSMWidget


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

        from traffic_control.forms import AdminEnumChoiceField

        if isinstance(db_field, (EnumField, EnumIntegerField)):
            return db_field.formfield(choices_form_class=AdminEnumChoiceField, **kwargs)

        return super().formfield_for_choice_field(db_field, request, **kwargs)


class UserStampedInlineAdminMixin:
    """
    A mixin class for model admin that sets inline model created_by/updated_by
    from request user
    """

    def save_formset(self, request, form, formset, change):
        # If there are deleted related models, commit changes,
        # else don't commit, as created_by field is filled to the object before saving.
        # This means that sometimes save might be called twice to objects.
        objects = formset.save(commit=len(formset.deleted_forms))

        for obj in objects:
            # Validate that object has a created_by field, and skip models such as Files
            if hasattr(obj, "created_by_id"):
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
                "query_string": changelist.get_query_string({self.parameter_name: lookup}, []),
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
    actions = ["action_soft_delete"]
    list_filter = [
        SoftDeleteFilter,
    ]

    def action_soft_delete(self, request, queryset):
        queryset.soft_delete(request.user)

    action_soft_delete.short_description = _("Mark selected objects as deleted")
    action_soft_delete.allowed_permissions = ("change", "delete")


class UpdatePlanLocationAdminMixin:
    """
    A mixin class for bulk-deleting planned devices to update their related Plan locations.
    """

    def delete_queryset(self, request, queryset):
        related_plan_ids = list(queryset.values_list("plan_id", flat=True).distinct())
        super().delete_queryset(request, queryset)
        related_plans = Plan.objects.filter(id__in=related_plan_ids, derive_location=True)
        for plan in related_plans:
            plan.derive_location_from_related_plans()


class DeviceTypeSearchAdminMixin:
    def get_search_fields(self, request):
        return self.search_fields + ("device_type__code", "device_type__legacy_code")

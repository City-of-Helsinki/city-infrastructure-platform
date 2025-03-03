from typing import Dict

from admin_confirm import AdminConfirmMixin
from django.contrib.admin import SimpleListFilter
from django.contrib.gis.forms import OSMWidget
from django.db.models import FileField, ImageField, ManyToManyField, Model
from django.forms import ModelForm
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


class CityInfraAdminConfirmMixin(AdminConfirmMixin):
    """Class for tweaking admin confirmation behaviour.
    Overwrite private _get_changed_data function to support fields only in admin form not in model itself.
    """

    only_form_fields = []

    def _get_changed_data(self, form: ModelForm, model: Model, obj: object, add: bool) -> Dict:
        """
        Given a form, detect the changes on the form from the default values (if add) or
        from the database values of the object (model instance)

        form - Submitted form that is attempting to alter the obj
        model - the model class of the obj
        obj - instance of model which is being altered
        add - are we attempting to add the obj or does it already exist in the database

        Returns a dictionary of the fields and their changed values if any
        """

        changed_data = {}
        if add:
            self._handle_add(form, model, changed_data)
        else:
            self._handle_change(form, model, changed_data, obj)

        return changed_data

    def _filtered_form_cleaned_data_items(self, form):
        return filter(lambda x: x[0] not in self.only_form_fields, form.cleaned_data.items())

    @staticmethod
    def _display_for_changed_data(field, initial_value, new_value):
        if not (isinstance(field, FileField) or isinstance(field, ImageField)):
            return [initial_value, new_value]

        if initial_value:
            if new_value is False:
                # Clear has been selected
                return [initial_value.name, None]
            elif new_value:
                return [initial_value.name, new_value.name]
            else:
                # No cover: Technically doesn't get called in current code because
                # This function is only called if there was a difference in the data
                return [initial_value.name, initial_value.name]  # pragma: no cover

        if new_value:
            return [None, new_value.name]

        return [None, None]

    def _handle_add(self, form, model, changed_data):
        for name, new_value in self._filtered_form_cleaned_data_items(form):
            # Don't consider default values as changed for adding
            field_object = model._meta.get_field(name)
            default_value = field_object.get_default()
            if new_value is not None and new_value != default_value:
                # Show what the default value is
                changed_data[name] = self._display_for_changed_data(field_object, default_value, new_value)

    def _handle_change(self, form, model, changed_data, obj):
        for name, new_value in self._filtered_form_cleaned_data_items(form):
            # Ignore fields that are only in admin for and not in the model itself
            # Since the form considers initial as the value first shown in the form
            # It could be incorrect when user hits save, and then hits "No, go back to edit"
            obj.refresh_from_db()

            field_object = model._meta.get_field(name)
            initial_value = getattr(obj, name)

            # Note: getattr does not work on ManyToManyFields
            if isinstance(field_object, ManyToManyField):
                initial_value = field_object.value_from_object(obj)

            if initial_value != new_value:
                changed_data[name] = self._display_for_changed_data(field_object, initial_value, new_value)

from typing import Any

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.gis.forms import OSMWidget
from django.db.models import Model
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from admin_helper.decorators import requires_fields
from map.services.inspect_link import build_map_view_inspect_url
from traffic_control.models.plan import Plan


class CityInfra3DOSMWidget(OSMWidget):
    """OSM map widget centred on Helsinki railway station with 3D geometry support.

    Uses Helsinki city raster tiles (maptiles.api.hel.fi) instead of the
    default tile.openstreetmap.org.  This fixes a Firefox-only 403: OpenLayers'
    ``crossOrigin='anonymous'`` puts Firefox into CORS mode and OSM's CDN
    blocks requests whose ``Origin`` header is a private/localhost domain.
    Helsinki's tile CDN supports CORS for all origins and requires no API key.
    """

    template_name = "gis/cityinfra-osm-with-inspect-link.html"
    default_lon = 24.9416259
    default_lat = 60.170255
    default_zoom = 12.5
    supports_3d = True
    map_view_inspect_url: str | None = None

    class Media:
        css = {"all": ("traffic_control/css/map_view_inspect_link.css",)}

    def get_context(self, name: str, value: Any, attrs: dict | None) -> dict:
        """Adds the map-view inspect link URL to the widget template context.

        Args:
            name (str): The form field name.
            value (Any): The geometry value.
            attrs (dict | None): The widget HTML attributes.

        Returns:
            dict: The template context.
        """
        context = super().get_context(name, value, attrs)
        context["map_view_inspect_url"] = self.map_view_inspect_url
        return context


class Geometry3DFieldAdminMixin:
    """A mixin class that shows a map for 3d geometries.

    Django's default behaviour is to use a text field for 3d geometries.
    The class must be used together with traffic_control.forms.Point3DFieldForm
    in order to save 3d geometry to model instances
    """

    gis_widget = CityInfra3DOSMWidget
    SHOW_Z_COORD = True

    def get_form(self, request: HttpRequest, obj: Model | None = None, change: bool = False, **kwargs: Any) -> type:
        """Returns the admin form with a map-view inspect link on the map widgets of a saved object.

        Args:
            request (HttpRequest): The current request.
            obj (Model | None): The object being edited, or None in the add view.
            change (bool): Whether the form is for the change view.
            **kwargs (Any): Passed on to ``ModelAdmin.get_form``.

        Returns:
            type: The model form class.
        """
        form = super().get_form(request, obj, change=change, **kwargs)
        if obj is not None:
            inspect_url = build_map_view_inspect_url(obj)
            for field in form.base_fields.values():
                if isinstance(field.widget, CityInfra3DOSMWidget):
                    field.widget.map_view_inspect_url = inspect_url
        return form

    def get_fieldsets(self, request, obj=None, **kwargs):
        fieldsets = super().get_fieldsets(request, obj, **kwargs)
        if not self.SHOW_Z_COORD:
            for _, fields in fieldsets:
                if "z_coord" in fields["fields"]:
                    temp_list = list(fields["fields"])
                    temp_list.remove("z_coord")
                    fields["fields"] = temp_list
        if obj is not None and not self.has_change_permission(request, obj):
            # Read-only change view: the form has no location field, so show a read-only map instead
            fieldsets = _replace_fieldset_field(fieldsets, "location", "location_map")
        return fieldsets

    @admin.display(description=_("Location (x,y)"))
    def location_map(self, obj: Model) -> str:
        """Renders the location of a read-only object as a non-editable map with the map-view inspect link.

        Args:
            obj (Model): The object shown in the read-only change view.

        Returns:
            str: The map widget HTML including the JavaScript and CSS it needs.
        """
        widget = obj._meta.get_field("location").formfield(widget=self.gis_widget).widget
        widget.attrs["disabled"] = True
        widget.map_view_inspect_url = build_map_view_inspect_url(obj)
        return format_html("{}{}", widget.media, widget.render("location", obj.location, attrs={"id": "id_location"}))


def _replace_fieldset_field(fieldsets: list, old_name: str, new_name: str) -> list:
    """Returns a copy of the fieldsets where a field name is replaced with another one.

    Args:
        fieldsets (list): The admin fieldsets as (name, options) pairs.
        old_name (str): The field name to replace.
        new_name (str): The field name to use instead.

    Returns:
        list: The new fieldsets. The given fieldsets are not modified.
    """
    return [
        (name, {**options, "fields": [new_name if field == old_name else field for field in options["fields"]]})
        for name, options in fieldsets
    ]


class PreviewImageFileFieldMixin:
    """
    Use this if your admin class is for a model that has a file field. Remember to add file_preview to the list_display
    field on your admin class. Assumes that the file is an image.
    """

    @staticmethod
    @admin.display(description=_("Image file preview"))
    def image_file_preview(obj):
        if obj.file and obj.file.url:
            icon_url = obj.file.url
            return format_html('<img src="{url}" width="50" height="50" />', url=icon_url)
        else:
            return None


class PreviewIconFileRelationMixin:
    """
    Use this if your admin class is for a model that has an icon_file field. Remember to add icon_preview to the
    list_display field on your admin class.
    """

    @staticmethod
    @admin.display(description=_("Icon preview"))
    def icon_preview(obj):
        if obj.icon_file and obj.icon_file.file and obj.icon_file.file.url:
            icon_url = obj.icon_file.file.url
            return format_html('<img src="{url}" width="50" height="50" />', url=icon_url)
        else:
            return None


class UploadsFileProxyMixin:
    @staticmethod
    @admin.display(description=_("File proxy"))
    def file_proxy(obj):
        """Returns the permission-controlled proxy link to the file."""
        if obj.file:
            return format_html('<a href="/uploads/{url}" target="_blank">{url}</a>', url=obj.file.name)
        else:
            return "-"


class PreviewDeviceTypeRelationMixin:
    """
    Use this if your admin class is for a model that has a device_type field. Remember to add device_type_preview to the
    list_display field on your admin class.
    """

    @staticmethod
    @admin.display(description=_("Device type preview"))
    @requires_fields("device_type", "device_type__icon_file", "device_type__icon_file__file")
    def device_type_preview(obj):
        device_type = obj.device_type
        if device_type and device_type.icon_file and device_type.icon_file.file and device_type.icon_file.file.url:
            icon_url = device_type.icon_file.file.url
            return format_html(
                """
            <div>
                <img src="{icon_url}" width="50" height="50" />
                <span>{name}</span>
            </div>
            """,
                icon_url=icon_url,
                name=str(device_type),
            )
        else:
            return device_type


class FormattedContentsAdminMixin:
    """
    A mixin class for model admin that shows formatted HTML contents in the admin change view.

    Returns nicely formatted HTML similar to the _content_s_rows.html template.
    """

    @requires_fields("get_content_s_rows")
    @admin.display(description=_("Content"))
    def content(self, obj):
        """
        Returns formatted HTML representation of content_s rows.

        Args:
            obj: The model instance with get_content_s_rows method.

        Returns:
            str: HTML formatted content or "-" if no content exists.
        """
        if not obj or not hasattr(obj, "get_content_s_rows"):
            return "-"

        context = {"content_s_rows": obj.get_content_s_rows()}
        return render_to_string("embed/_content_s_rows.html", context)


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

    readonly_fields = ("deleted_at", "deleted_by", "is_active")
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

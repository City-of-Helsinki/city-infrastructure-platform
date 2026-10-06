import json

from django.conf import settings
from django.contrib.admin import site as admin_site, widgets
from django.contrib.gis import forms
from django.contrib.gis.geos import GEOSGeometry, WKTWriter
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms.models import BaseInlineFormSet, ModelChoiceIteratorValue
from django.forms.widgets import Select
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import get_language, gettext_lazy as _
from enumfields.forms import EnumChoiceField

from city_furniture.models import FurnitureSignpostPlan
from traffic_control.geometry_utils import geometry_is_legit, get_3d_geometry, get_z_for_geometry, is_simple_geometry
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    BarrierPlan,
    BarrierReal,
    MountPlan,
    MountReal,
    OperationalArea,
    Plan,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficControlDeviceType,
    TrafficControlDeviceTypeIcon,
    TrafficControlDeviceTypeTag,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.services.virus_scan import add_virus_scan_errors_to_auditlog, get_error_details_message
from traffic_control.utils import get_file_upload_obstacles, get_icon_upload_obstacles
from traffic_control.validators import validate_location_ewkt, validate_structured_content


class AdminFileWidgetWithProxy(widgets.AdminFileWidget):
    """
    File widget that opens the uploaded file in a new tab.
    """

    template_name = "admin/traffic_control/widgets/clearable_file_input.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        if value and hasattr(value, "name"):
            context["widget"]["file_proxy"] = f"/uploads/{value.name}"

        return context


class AbstractAdminDeviceTypeIconSelectWidget(Select):
    """
    Widget that show a traffic sign icon representing the selected device type
    next to the select input
    """

    template_name = "admin/traffic_control/widgets/traffic_sign_icon_select.html"
    device_type_icon_model = None

    class Media:
        css = {"all": ("traffic_control/css/traffic_sign_icon_select.css",)}
        js = ("traffic_control/js/traffic_sign_icon_select.js",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon_url_mapping = None
        if self.device_type_icon_model is None:
            raise NotImplementedError("Inherited class is missing Model declaration")

    def get_icon_url(self, value):
        if not self.icon_url_mapping:
            self.icon_url_mapping = {}
            icons = self.device_type_icon_model.objects.all().only("id", "file")
            for icon in icons:
                self.icon_url_mapping[icon.id] = icon.file.url
        return self.icon_url_mapping.get(value, "")

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["icon_path"] = self.get_icon_url(value)
        return context

    def create_option(self, name, value, *args, **kwargs):
        if isinstance(value, ModelChoiceIteratorValue):
            value = value.value
        option = super().create_option(name, value, *args, **kwargs)
        option["attrs"]["icon-url"] = self.get_icon_url(value)
        return option


class AdminTrafficControlDeviceTypeIconSelectWidget(AbstractAdminDeviceTypeIconSelectWidget):
    device_type_icon_model = TrafficControlDeviceTypeIcon


class AdminStructuredContentWidget(forms.Widget):
    """
    Widget that presents structured content with JSON Editor instead of plain JSON.
    JSON Editor provides also validation for the content.
    """

    template_name = "admin/traffic_control/widgets/structured_content_widget.html"

    def render(self, name, value, device_type_name="device_type", attrs=None, renderer=None):
        context = {
            "name": name,
            "data": value,
            "device_type_name": device_type_name,
            "devices_api_url": reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": "__id__"}),
        }
        return render_to_string(self.template_name, context)

    class Media:
        css = {"all": ("traffic_control/css/structured_content_widget.css",)}
        js = (
            "https://cdn.jsdelivr.net/npm/@json-editor/json-editor@2.8.0/dist/jsoneditor.js",
            "traffic_control/js/structured_content_widget.js",
        )


class AdminEnumSelectWidget(Select):
    """
    Widget that that displays Enum's logical value in the option label after
    the label defined in Enum class.
    """

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        value = option["value"]
        if value:
            label = option["label"]
            option["label"] = f"{label} ({value})"
        return option


class AdminEnumChoiceField(EnumChoiceField):
    """
    Form field that that displays Enum's logical value in the option label
    after the label defined in Enum class.
    """

    widget = AdminEnumSelectWidget


class StructuredContentModelFormMixin:
    """
    Validate structured content field against device type's content schema.
    Raises `ValidationError` if content is invalid.
    """

    def clean(self):
        validation_errors = {}

        # Validate content according to device type's schema
        cleaned_data = super().clean()
        if "content_s" in cleaned_data:
            content = cleaned_data.get("content_s")
            device_type = cleaned_data.get("device_type")
            missing_content = cleaned_data.get("missing_content")

            if missing_content and content is not None:
                validation_errors["missing_content"] = _(
                    "'Missing content' cannot be enabled when the content field (content_s) is not empty."
                )
            if not missing_content:
                errors = validate_structured_content(content, device_type)
                if errors:
                    validation_errors["content_s"] = errors

        if len(validation_errors) > 0:
            raise ValidationError(validation_errors)

        return cleaned_data


class SRIDBoundGeometryFormMixin:
    def clean(self):
        cleaned_data = super().clean()
        if "location" in cleaned_data:
            location = cleaned_data.get("location")
            if location and not geometry_is_legit(GEOSGeometry(location)):
                raise ValidationError({"location": f"Invalid location: {location}"})
        return cleaned_data


class Geometry3DFieldForm(forms.ModelForm):
    """Form class that allows entering a z coordinate for 3d point and location in ewkt format"""

    z_coord = forms.FloatField(label=_("Location (z)"), initial=0, required=False)
    location_ewkt = forms.CharField(label=_("Location (EWKT)"), widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Form is in read-only mode, so the field doesn't exist
        if "location" not in self.fields:
            return

        self.fields["location"].label = _("Location (x,y)")
        self.fields["location_ewkt"].validators.append(validate_location_ewkt)
        if self.instance.location:
            self.fields["z_coord"].initial = get_z_for_geometry(self.instance.location)
            self.fields["location_ewkt"].initial = self.instance.location.ewkt

    def clean(self):
        cleaned_data = super().clean()
        z_coord = cleaned_data.pop("z_coord", 0) or 0
        location = cleaned_data.get("location", None)
        location_ewkt = cleaned_data.get("location_ewkt", None)
        new_geom = self._get_new_geom(location, location_ewkt, z_coord)
        has_location_error = True if "location" in self.errors else False
        if new_geom:
            if has_location_error:
                del self.errors["location"]
            cleaned_data["location"] = new_geom
            cleaned_data["location_ewkt"] = new_geom.ewkt
        else:
            if not location_ewkt and self.instance:
                # this is update with clearing location_ewkt field
                cleaned_data["location_ewkt"] = ""
                cleaned_data["location"] = None
            # sometimes mapwidget rounds coordinates differently
            # in _get_new_geom check is done using 6 digits so when new_geom is None, location in new_geom need to be
            # set to self.instance.location to prevent unnecessary auditlog entries on save.
            elif not has_location_error:
                cleaned_data["location"] = self.instance.location

        return cleaned_data

    def _get_new_geom(self, location, location_ewkt, z_coord):
        """Get new location. On create location_ewkt is the first priority
        If updating value coming from widget is not allowed for complex geometries, eg. Points and Polygons can be.
        """
        location_ewkt_changed = (not self.instance.location and location_ewkt) or (
            location_ewkt and location_ewkt != self.instance.location.ewkt
        )
        location_changed = self._get_is_location_changed(location)
        if not location_ewkt_changed and not location_changed:
            return None

        if not self.instance.location:
            if location_ewkt:
                return GEOSGeometry(location_ewkt)
            else:
                return get_3d_geometry(location, z_coord)
        if location_ewkt_changed:
            return GEOSGeometry(location_ewkt)
        if location_changed and not location_ewkt_changed:
            if is_simple_geometry(location):
                return get_3d_geometry(location, z_coord)
            else:
                raise ValidationError(
                    {
                        "location": _(
                            "Changing location from map is not allowed for geometry '%(geometry_type)s'"
                            % {"geometry_type": location.__class__.__name__}
                        )
                    }
                )
        return get_3d_geometry(location, z_coord)

    def _get_is_location_changed(self, location):
        """location, coming from map widget has different precision compared to what is in our database,
        so comparison needs to be done with the same precision, 6 should enough as it is micrometers.
        """
        wkt_w = WKTWriter(precision=6, trim=True, dim=3)

        location_wkt = wkt_w.write(location) if location else None
        instance_wkt = wkt_w.write(self.instance.location) if self.instance.location else None
        return location_wkt != instance_wkt


class AdditionalSignRealModelForm(StructuredContentModelFormMixin, SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = AdditionalSignReal
        fields = "__all__"
        widgets = {
            "content_s": AdminStructuredContentWidget,
        }


class AdditionalSignPlanModelForm(StructuredContentModelFormMixin, SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = AdditionalSignPlan
        fields = "__all__"
        widgets = {
            "content_s": AdminStructuredContentWidget,
        }


class BarrierPlanModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = BarrierPlan
        fields = "__all__"


class BarrierRealModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = BarrierReal
        fields = "__all__"


class MountPlanModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = MountPlan
        fields = "__all__"


class MountRealModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = MountReal
        fields = "__all__"


class OperationalModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = OperationalArea
        fields = "__all__"


class PlanModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = Plan
        fields = "__all__"


class RoadMarkingPlanModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = RoadMarkingPlan
        fields = "__all__"


class RoadMarkingRealModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = RoadMarkingReal
        fields = "__all__"


class SignpostPlanModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = SignpostPlan
        fields = "__all__"


class SignpostRealModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = SignpostReal
        fields = "__all__"


class OrderedByIconFileFieldForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "icon_file" in self.fields:
            self.fields["icon_file"].queryset = self.fields["icon_file"].queryset.order_by("file")

    class Meta:
        abstract = True


class TrafficControlDeviceTypeForm(OrderedByIconFileFieldForm):
    class Meta:
        model = TrafficControlDeviceType
        widgets = {
            "icon_file": AdminTrafficControlDeviceTypeIconSelectWidget,
        }
        fields = "__all__"


# English is intentionally missing, because select2 is in English without a translation file.
SELECT2_LANGUAGES = {"fi": "fi", "sv": "sv"}


def get_select2_language() -> str:
    """Resolve the select2 translation file matching the active language.

    Returns:
        str: Language code of the select2 translation file, or an empty string when the active
            language needs no translation file.
    """
    return SELECT2_LANGUAGES.get(get_language(), "")


class DeviceTypeAutocompleteSelectMultiple(forms.SelectMultiple):
    """Select2 autocomplete widget for picking device types on the device type tag admin page.

    The widget is self-contained instead of built on Django's undocumented admin autocomplete
    widgets, because the selection is made through a reverse many-to-many relation, which those
    widgets and the shared admin autocomplete endpoint do not support. Only the admin's bundled
    select2 assets are reused, so the rendered user interface is the standard admin one.
    """

    url_name = "%s:traffic_control_trafficcontroldevicetypetag_devicetype_autocomplete"
    source_app_label = TrafficControlDeviceTypeTag._meta.app_label
    source_model_name = TrafficControlDeviceTypeTag._meta.model_name
    source_field_name = "device_types"

    def __init__(self, admin_site, attrs: dict = None, choices: tuple = ()):
        """Initialize the widget.

        Args:
            admin_site (AdminSite): Admin site that registers the autocomplete endpoint.
            attrs (dict): Extra html attributes of the rendered select element.
            choices (tuple): Initial choices of the select element.
        """
        self.admin_site = admin_site
        super().__init__(attrs=attrs, choices=choices)

    def get_url(self) -> str:
        """Resolve the url of the device type autocomplete endpoint.

        Returns:
            str: Url that select2 queries for the matching device types.
        """
        return reverse(self.url_name % self.admin_site.name)

    def build_attrs(self, base_attrs: dict, extra_attrs: dict = None) -> dict:
        """Add the html attributes that the admin's select2 initialization reads.

        Args:
            base_attrs (dict): Attributes defined on the widget.
            extra_attrs (dict): Attributes defined on the rendered field.

        Returns:
            dict: Html attributes of the rendered select element.
        """
        attrs = super().build_attrs(base_attrs, extra_attrs=extra_attrs)
        css_classes = [css_class for css_class in (attrs.get("class"), "admin-autocomplete") if css_class]
        attrs.update(
            {
                "class": " ".join(css_classes),
                "data-ajax--cache": "true",
                "data-ajax--delay": 250,
                "data-ajax--type": "GET",
                "data-ajax--url": self.get_url(),
                "data-app-label": self.source_app_label,
                "data-model-name": self.source_model_name,
                "data-field-name": self.source_field_name,
                "data-theme": "admin-autocomplete",
                "data-allow-clear": json.dumps(not self.is_required),
                "data-placeholder": "",
                "lang": get_select2_language(),
            }
        )

        return attrs

    def optgroups(self, name: str, value: list, attr: dict = None) -> list:
        """Render only the selected device types, as the rest are fetched by select2 on demand.

        Args:
            name (str): Name of the rendered field.
            value (list): Primary keys of the selected device types.
            attr (dict): Html attributes of the rendered select element.

        Returns:
            list: Single option group holding the selected device types.
        """
        selected = {str(pk) for pk in value if str(pk) not in self.choices.field.empty_values}
        options = [
            self.create_option(name, device_type.pk, self.choices.field.label_from_instance(device_type), True, index)
            for index, device_type in enumerate(self.choices.queryset.filter(pk__in=selected))
        ]

        return [(None, options, 0)]

    @property
    def media(self) -> forms.Media:
        """Collect the select2 assets shipped with the Django admin.

        Returns:
            forms.Media: Javascript and css files needed by the widget.
        """
        extra = "" if settings.DEBUG else ".min"
        language = get_select2_language()
        i18n_file = (f"admin/js/vendor/select2/i18n/{language}.js",) if language else ()

        return forms.Media(
            js=(
                f"admin/js/vendor/jquery/jquery{extra}.js",
                f"admin/js/vendor/select2/select2.full{extra}.js",
            )
            + i18n_file
            + (
                "admin/js/jquery.init.js",
                "admin/js/autocomplete.js",
            ),
            css={
                "screen": (
                    f"admin/css/vendor/select2/select2{extra}.css",
                    "admin/css/autocomplete.css",
                ),
            },
        )


class TrafficControlDeviceTypeTagForm(forms.ModelForm):
    """Tag form that allows selecting the device types carrying the tag."""

    device_types = forms.ModelMultipleChoiceField(
        queryset=TrafficControlDeviceType.objects.all(),
        required=False,
        label=_("Device types"),
        help_text=_("Device types that have this tag."),
        widget=DeviceTypeAutocompleteSelectMultiple(admin_site),
    )

    class Meta:
        model = TrafficControlDeviceTypeTag
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["device_types"].initial = self.instance.device_types.all()

    def save(self, commit=True) -> TrafficControlDeviceTypeTag:
        """Save the tag and update the device types it is attached to.

        Args:
            commit (bool): Whether the tag and its relations are saved immediately.

        Returns:
            TrafficControlDeviceTypeTag: The saved tag instance.
        """
        instance = super().save(commit=commit)

        if commit:
            self._update_device_types(instance)
        else:
            original_save_m2m = self.save_m2m

            def save_m2m() -> None:
                original_save_m2m()
                self._update_device_types(instance)

            self.save_m2m = save_m2m

        return instance

    def _update_device_types(self, tag: TrafficControlDeviceTypeTag) -> None:
        """Attach the tag to the selected device types and detach it from the unselected ones.

        Relations are updated from the device type side, so that the change is written to the
        audit log of each affected device type.

        Args:
            tag (TrafficControlDeviceTypeTag): The tag being saved.
        """
        selected = set(self.cleaned_data.get("device_types") or [])
        current = set(tag.device_types.all())

        for device_type in selected - current:
            device_type.tags.add(tag)

        for device_type in current - selected:
            device_type.tags.remove(tag)


class AbstractDeviceTypeIconForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        if file:
            illegal_file_types, virus_scan_errors, existing_icons = get_icon_upload_obstacles([file])
            if existing_icons:
                raise ValidationError(_(f"Icon with name '{', '.join(existing_icons)}' already exists."))

            if illegal_file_types:
                raise ValidationError(_(f"Illegal file types: {', '.join(illegal_file_types)}"))

            if virus_scan_errors:
                add_virus_scan_errors_to_auditlog(virus_scan_errors, None, self._meta.model, None)
                raise ValidationError(_(f"Virus scan failure: {get_error_details_message(virus_scan_errors)}"))
        return cleaned_data

    def save(self, commit=True):
        file = self.cleaned_data.get("file")
        if file and self.has_changed() and "file" in self.changed_data:
            pass

        return super().save(commit=commit)


class TrafficControlDeviceTypeIconForm(AbstractDeviceTypeIconForm):
    class Meta:
        model = TrafficControlDeviceTypeIcon
        fields = "__all__"


class TrafficLightPlanModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = TrafficLightPlan
        fields = "__all__"


class TrafficLightRealModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = TrafficLightReal
        fields = "__all__"


class TrafficSignPlanModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = TrafficSignPlan
        fields = "__all__"


class TrafficSignRealModelForm(SRIDBoundGeometryFormMixin, Geometry3DFieldForm):
    class Meta:
        model = TrafficSignReal
        fields = "__all__"


class PlanRelationsForm(forms.Form):
    barrier_plans = forms.ModelMultipleChoiceField(
        BarrierPlan.objects.active(),
        required=False,
        widget=widgets.FilteredSelectMultiple(verbose_name=_("Barrier Plans"), is_stacked=False),
    )
    mount_plans = forms.ModelMultipleChoiceField(
        MountPlan.objects.active(),
        required=False,
        widget=widgets.FilteredSelectMultiple(verbose_name=_("Mount Plans"), is_stacked=False),
    )
    road_marking_plans = forms.ModelMultipleChoiceField(
        RoadMarkingPlan.objects.active(),
        required=False,
        widget=widgets.FilteredSelectMultiple(verbose_name=_("Road Marking Plans"), is_stacked=False),
    )
    signpost_plans = forms.ModelMultipleChoiceField(
        SignpostPlan.objects.active(),
        required=False,
        widget=widgets.FilteredSelectMultiple(verbose_name=_("Signpost Plans"), is_stacked=False),
    )
    traffic_light_plans = forms.ModelMultipleChoiceField(
        TrafficLightPlan.objects.active(),
        required=False,
        widget=widgets.FilteredSelectMultiple(verbose_name=_("Traffic Light Plans"), is_stacked=False),
    )
    traffic_sign_plans = forms.ModelMultipleChoiceField(
        TrafficSignPlan.objects.active(),
        required=False,
        widget=widgets.FilteredSelectMultiple(verbose_name=_("Traffic Sign Plans"), is_stacked=False),
    )
    additional_sign_plans = forms.ModelMultipleChoiceField(
        AdditionalSignPlan.objects.all(),
        required=False,
        widget=widgets.FilteredSelectMultiple(verbose_name=_("Additional Sign Plans"), is_stacked=False),
    )
    furniture_signpost_plans = forms.ModelMultipleChoiceField(
        FurnitureSignpostPlan.objects.active(),
        required=False,
        widget=widgets.FilteredSelectMultiple(verbose_name=_("Furniture Signpost Plans"), is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        plan = kwargs.pop("plan")

        super().__init__(*args, **kwargs)

        # Omit instances related to other plans from choices.
        for field_name, field in self.fields.items():
            field.queryset = field.queryset.filter(Q(plan=None) | Q(plan=plan))

            # Optimize listing all plans. Devices have device type code and description in their "name",
            # except mount which have its mount type.
            if hasattr(field.queryset.model, "device_type"):
                field.queryset = field.queryset.select_related("device_type")
            elif hasattr(field.queryset.model, "mount_type"):
                field.queryset = field.queryset.select_related("mount_type")


class CityInfraFileUploadFormset(BaseInlineFormSet):
    def clean(self):
        if self.files:
            illegal_file_types, virus_scan_errors = get_file_upload_obstacles(self.files)
            if illegal_file_types:
                raise ValidationError(f"Illegal file types: {illegal_file_types}")
            if virus_scan_errors:
                add_virus_scan_errors_to_auditlog(virus_scan_errors, None, self.model, None)
                raise ValidationError(f"Virus scan failure: {get_error_details_message(virus_scan_errors)}")
        super().clean()

from django.conf import settings
from django.contrib.admin import widgets
from django.contrib.gis import forms
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms.models import BaseInlineFormSet, ModelChoiceIteratorValue
from django.forms.widgets import Select
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from enumfields.forms import EnumChoiceField

from city_furniture.models import FurnitureSignpostPlan
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    BarrierPlan,
    MountPlan,
    RoadMarkingPlan,
    SignpostPlan,
    TrafficControlDeviceType,
    TrafficLightPlan,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.services.virus_scan import add_virus_scan_errors_to_auditlog, get_error_details_message
from traffic_control.utils import get_file_upload_obstacles
from traffic_control.validators import validate_structured_content


class AdminFileWidget(widgets.AdminFileWidget):
    """
    File widget that opens the uploaded file in a new tab.
    """

    template_name = "admin/traffic_control/widgets/clearable_file_input.html"


class AdminTrafficSignIconSelectWidget(Select):
    """
    Widget that show a traffic sign icon representing the selected device type
    next to the select input
    """

    template_name = "admin/traffic_control/widgets/traffic_sign_icon_select.html"

    class Media:
        css = {"all": ("traffic_control/css/traffic_sign_icon_select.css",)}
        js = ("traffic_control/js/traffic_sign_icon_select.js",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon_url_mapping = None

    def get_icon_url(self, value):
        if not self.icon_url_mapping:
            self.icon_url_mapping = {}
            device_types = TrafficControlDeviceType.objects.all().only("id", "icon")
            for device_type in device_types:
                icons = device_type.get_icons()
                if icons:
                    self.icon_url_mapping[device_type.id] = icons["svg"]
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
        return mark_safe(render_to_string(self.template_name, context))

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


class Point3DFieldForm(forms.ModelForm):
    """Form class that allows entering a z coordinate for 3d point"""

    z_coord = forms.FloatField(label=_("Location (z)"), initial=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Form is in read-only mode, so the field doesn't exist
        if "location" not in self.fields:
            return

        self.fields["location"].label = _("Location (x,y)")
        if self.instance.location:
            self.fields["z_coord"].initial = self.instance.location.z

    def clean(self):
        cleaned_data = super().clean()
        if "location" in cleaned_data:
            z_coord = cleaned_data.pop("z_coord", 0)
            location = cleaned_data["location"]
            cleaned_data["location"] = Point(location.x, location.y, z_coord, srid=settings.SRID)
        return cleaned_data


class TrafficSignRealModelForm(Point3DFieldForm):
    class Meta:
        model = TrafficSignReal
        fields = "__all__"
        widgets = {
            "device_type": AdminTrafficSignIconSelectWidget,
        }


class TrafficSignPlanModelForm(Point3DFieldForm):
    class Meta:
        model = TrafficSignPlan
        fields = "__all__"
        widgets = {
            "device_type": AdminTrafficSignIconSelectWidget,
        }


class AdditionalSignRealModelForm(StructuredContentModelFormMixin, Point3DFieldForm):
    class Meta:
        model = AdditionalSignReal
        fields = "__all__"
        widgets = {
            "device_type": AdminTrafficSignIconSelectWidget,
            "content_s": AdminStructuredContentWidget,
        }


class AdditionalSignPlanModelForm(StructuredContentModelFormMixin, Point3DFieldForm):
    class Meta:
        model = AdditionalSignPlan
        fields = "__all__"
        widgets = {
            "device_type": AdminTrafficSignIconSelectWidget,
            "content_s": AdminStructuredContentWidget,
        }


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

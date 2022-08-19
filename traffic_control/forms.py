from django.conf import settings
from django.contrib.admin import widgets
from django.contrib.gis import forms
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms.models import ModelChoiceIteratorValue
from django.forms.widgets import Select
from django.utils.translation import gettext_lazy as _
from enumfields.forms import EnumChoiceField

from traffic_control.models import (
    AdditionalSignContentPlan,
    AdditionalSignContentReal,
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
            id_icon_values = TrafficControlDeviceType.objects.values_list("id", "icon")
            for uuid, icon in id_icon_values:
                if icon:
                    icon_name = icon.rsplit(".", maxsplit=1)[0]
                    icon_path = f"{settings.STATIC_URL}traffic_control/svg/traffic_sign_icons/{icon_name.upper()}.svg"
                    self.icon_url_mapping[uuid] = icon_path
        return self.icon_url_mapping.get(value, "")

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["icon_path"] = self.get_icon_url(value)
        return context

    def create_option(self, name, value, *args, **kwargs):
        if type(value) == ModelChoiceIteratorValue:
            value = value.value
        option = super().create_option(name, value, *args, **kwargs)
        option["attrs"]["icon-url"] = self.get_icon_url(value)
        return option


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
        }


class AdditionalSignPlanModelForm(StructuredContentModelFormMixin, Point3DFieldForm):
    class Meta:
        model = AdditionalSignPlan
        fields = "__all__"
        widgets = {
            "device_type": AdminTrafficSignIconSelectWidget,
        }


class AdditionalSignContentPlanForm(forms.ModelForm):
    class Meta:
        model = AdditionalSignContentPlan
        fields = "__all__"
        widgets = {
            "device_type": AdminTrafficSignIconSelectWidget,
        }


class AdditionalSignContentRealForm(forms.ModelForm):
    class Meta:
        model = AdditionalSignContentReal
        fields = "__all__"
        widgets = {
            "device_type": AdminTrafficSignIconSelectWidget,
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

    def __init__(self, *args, **kwargs):
        plan = kwargs.pop("plan")

        super().__init__(*args, **kwargs)

        # Omit instances related to other plans from choices.
        for field_name, field in self.fields.items():
            field.queryset = field.queryset.filter(Q(plan=None) | Q(plan=plan))

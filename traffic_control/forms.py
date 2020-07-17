from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.gis import forms
from django.contrib.gis.geos import Point
from django.db.models import Q
from django.forms.widgets import Select
from django.utils.translation import gettext_lazy as _
from enumfields.forms import EnumChoiceField

from .models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    BarrierPlan,
    MountPlan,
    RoadMarkingPlan,
    SignpostPlan,
    TrafficLightPlan,
    TrafficSignPlan,
    TrafficSignReal,
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


class Point3DFieldForm(forms.ModelForm):
    """Form class that allows entering a z coordinate for 3d point"""

    z_coord = forms.FloatField(label=_("Location (z)"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["location"].label = _("Location (x,y)")
        if self.instance.location:
            self.fields["z_coord"].initial = self.instance.location.z

    def clean(self):
        cleaned_data = super().clean()
        z_coord = cleaned_data.pop("z_coord", 0)
        location = cleaned_data["location"]
        cleaned_data["location"] = Point(
            location.x, location.y, z_coord, srid=settings.SRID
        )
        return cleaned_data


class TrafficSignRealModelForm(Point3DFieldForm):
    class Meta:
        model = TrafficSignReal
        fields = "__all__"


class TrafficSignPlanModelForm(Point3DFieldForm):
    class Meta:
        model = TrafficSignPlan
        fields = "__all__"


class AdditionalSignRealModelForm(Point3DFieldForm):
    class Meta:
        model = AdditionalSignReal
        fields = "__all__"


class AdditionalSignPlanModelForm(Point3DFieldForm):
    class Meta:
        model = AdditionalSignPlan
        fields = "__all__"


class PlanRelationsForm(forms.Form):
    barrier_plans = forms.ModelMultipleChoiceField(
        BarrierPlan.objects.active(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_("Barrier Plans"), is_stacked=False
        ),
    )
    mount_plans = forms.ModelMultipleChoiceField(
        MountPlan.objects.active(),
        required=False,
        widget=FilteredSelectMultiple(verbose_name=_("Mount Plans"), is_stacked=False),
    )
    road_marking_plans = forms.ModelMultipleChoiceField(
        RoadMarkingPlan.objects.active(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_("Road Marking Plans"), is_stacked=False
        ),
    )
    signpost_plans = forms.ModelMultipleChoiceField(
        SignpostPlan.objects.active(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_("Signpost Plans"), is_stacked=False
        ),
    )
    traffic_light_plans = forms.ModelMultipleChoiceField(
        TrafficLightPlan.objects.active(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_("Traffic Light Plans"), is_stacked=False
        ),
    )
    traffic_sign_plans = forms.ModelMultipleChoiceField(
        TrafficSignPlan.objects.active(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_("Traffic Sign Plans"), is_stacked=False
        ),
    )
    additional_sign_plans = forms.ModelMultipleChoiceField(
        AdditionalSignPlan.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_("Additional Sign Plans"), is_stacked=False
        ),
    )

    def __init__(self, *args, **kwargs):
        plan = kwargs.pop("plan")

        super().__init__(*args, **kwargs)

        # Omit instances related to other plans from choices.
        for field_name, field in self.fields.items():
            field.queryset = field.queryset.filter(Q(plan=None) | Q(plan=plan))

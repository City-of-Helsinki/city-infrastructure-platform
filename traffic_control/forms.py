from django.conf import settings
from django.contrib.gis import forms
from django.contrib.gis.geos import Point
from django.utils.translation import gettext_lazy as _

from .models import TrafficSignPlan, TrafficSignReal


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

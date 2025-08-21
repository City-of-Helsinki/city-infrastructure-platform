
from django import forms
from django.forms.models import ModelChoiceIteratorValue

from city_furniture.models import CityFurnitureDeviceType, FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureDeviceTypeIcon
from traffic_control.admin.utils import ResponsibleEntityPermissionAdminFormMixin
from traffic_control.forms import Geometry3DFieldForm, SRIDBoundGeometryFormMixin


class AdminCityFurnitureDeviceTypeIconSelectWidget(forms.Select):
    """
    Widget that allows a site administrator to choose a city furniture device type
    and see a preview of the corresponding icon
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
            icons = CityFurnitureDeviceTypeIcon.objects.all().only("id", "file")
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


class CityFurnitureDeviceTypeForm(forms.ModelForm):
    class Meta:
        model = CityFurnitureDeviceType
        widgets = {
            "icon_file": AdminCityFurnitureDeviceTypeIconSelectWidget,
        }
        fields = "__all__"

class FurnitureSignpostRealModelForm(
    SRIDBoundGeometryFormMixin, ResponsibleEntityPermissionAdminFormMixin, Geometry3DFieldForm
):
    class Meta:
        model = FurnitureSignpostReal
        fields = "__all__"


class FurnitureSignpostPlanModelForm(
    SRIDBoundGeometryFormMixin, ResponsibleEntityPermissionAdminFormMixin, Geometry3DFieldForm
):
    class Meta:
        model = FurnitureSignpostPlan
        fields = "__all__"

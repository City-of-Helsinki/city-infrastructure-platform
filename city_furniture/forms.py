from django import forms

from city_furniture.models import CityFurnitureDeviceType, FurnitureSignpostPlan, FurnitureSignpostReal
from traffic_control.admin.utils import ResponsibleEntityPermissionAdminFormMixin
from traffic_control.forms import Geometry3DFieldForm, SRIDBoundGeometryFormMixin


class AdminCityFurnitureDeviceTypeIconSelectWidget(forms.Select):
    """
    TODO
    """

    template_name = "admin/traffic_control/widgets/city_furniture_device_type_icon_select.html"

    class Media:
        css = {"all": ()}
        js = ()



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

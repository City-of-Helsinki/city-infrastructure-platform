from django import forms

from city_furniture.models import CityFurnitureDeviceType, FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureDeviceTypeIcon
from traffic_control.admin.utils import ResponsibleEntityPermissionAdminFormMixin
from traffic_control.forms import (
    AbstractAdminDeviceTypeIconSelectWidget,
    AbstractAdminDeviceTypeSelectWithIcon,
    AbstractDeviceTypeIconForm,
    Geometry3DFieldForm,
    SRIDBoundGeometryFormMixin,
)


class AdminCityFurnitureDeviceTypeIconSelectWidget(AbstractAdminDeviceTypeIconSelectWidget):
    device_type_icon_model = CityFurnitureDeviceTypeIcon


class AdminFurnitureDeviceTypeSelectWithIcon(AbstractAdminDeviceTypeSelectWithIcon):
    device_type_model = CityFurnitureDeviceType


class CityFurnitureDeviceTypeIconForm(AbstractDeviceTypeIconForm):
    class Meta:
        model = CityFurnitureDeviceTypeIcon
        fields = "__all__"


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
        widgets = {
            "device_type": AdminFurnitureDeviceTypeSelectWithIcon,
        }


class FurnitureSignpostPlanModelForm(
    SRIDBoundGeometryFormMixin, ResponsibleEntityPermissionAdminFormMixin, Geometry3DFieldForm
):
    class Meta:
        model = FurnitureSignpostPlan
        fields = "__all__"
        widgets = {
            "device_type": AdminFurnitureDeviceTypeSelectWithIcon,
        }

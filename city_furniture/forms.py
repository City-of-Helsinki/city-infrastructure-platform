from city_furniture.models import CityFurnitureDeviceType, FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureDeviceTypeIcon
from traffic_control.admin.utils import ResponsibleEntityPermissionAdminFormMixin
from traffic_control.forms import (
    AbstractAdminDeviceTypeIconSelectWidget,
    AbstractDeviceTypeIconForm,
    Geometry3DFieldForm,
    OrderedByIconFileFieldForm,
    SRIDBoundGeometryFormMixin,
)


class AdminCityFurnitureDeviceTypeIconSelectWidget(AbstractAdminDeviceTypeIconSelectWidget):
    device_type_icon_model = CityFurnitureDeviceTypeIcon


class CityFurnitureDeviceTypeIconForm(AbstractDeviceTypeIconForm):
    class Meta:
        model = CityFurnitureDeviceTypeIcon
        fields = "__all__"


class CityFurnitureDeviceTypeForm(OrderedByIconFileFieldForm):
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

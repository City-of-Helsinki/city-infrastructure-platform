from city_furniture.admin.utils import ResponsibleEntityPermissionAdminFormMixin
from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from traffic_control.forms import Point3DFieldForm


class FurnitureSignpostRealModelForm(ResponsibleEntityPermissionAdminFormMixin, Point3DFieldForm):
    class Meta:
        model = FurnitureSignpostReal
        fields = "__all__"


class FurnitureSignpostPlanModelForm(ResponsibleEntityPermissionAdminFormMixin, Point3DFieldForm):
    class Meta:
        model = FurnitureSignpostPlan
        fields = "__all__"

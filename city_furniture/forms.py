from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from traffic_control.admin.utils import ResponsibleEntityPermissionAdminFormMixin
from traffic_control.forms import Point3DFieldForm, SRIDBoundGeometryFormMixin


class FurnitureSignpostRealModelForm(
    SRIDBoundGeometryFormMixin, ResponsibleEntityPermissionAdminFormMixin, Point3DFieldForm
):
    class Meta:
        model = FurnitureSignpostReal
        fields = "__all__"


class FurnitureSignpostPlanModelForm(
    SRIDBoundGeometryFormMixin, ResponsibleEntityPermissionAdminFormMixin, Point3DFieldForm
):
    class Meta:
        model = FurnitureSignpostPlan
        fields = "__all__"

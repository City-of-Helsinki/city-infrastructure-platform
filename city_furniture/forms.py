from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from traffic_control.forms import Point3DFieldForm


class FurnitureSignpostRealModelForm(Point3DFieldForm):
    class Meta:
        model = FurnitureSignpostReal
        fields = "__all__"


class FurnitureSignpostPlanModelForm(Point3DFieldForm):
    class Meta:
        model = FurnitureSignpostPlan
        fields = "__all__"

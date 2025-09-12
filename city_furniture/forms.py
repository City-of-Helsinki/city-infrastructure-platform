from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from city_furniture.models import CityFurnitureDeviceType, FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureDeviceTypeIcon
from traffic_control.admin.utils import ResponsibleEntityPermissionAdminFormMixin
from traffic_control.forms import (
    AbstractAdminDeviceTypeIconSelectWidget,
    Geometry3DFieldForm,
    SRIDBoundGeometryFormMixin,
)
from traffic_control.services.virus_scan import add_virus_scan_errors_to_auditlog, get_error_details_message
from traffic_control.utils import get_icon_upload_obstacles


class AdminCityFurnitureDeviceTypeIconSelectWidget(AbstractAdminDeviceTypeIconSelectWidget):
    MODEL = CityFurnitureDeviceTypeIcon


class CityFurnitureDeviceTypeIconForm(forms.ModelForm):
    class Meta:
        model = CityFurnitureDeviceTypeIcon
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")

        if file:
            illegal_file_types, virus_scan_errors = get_icon_upload_obstacles([file])

            if illegal_file_types:
                raise ValidationError(_(f"Illegal file types: {', '.join(illegal_file_types)}"))

            if virus_scan_errors:
                add_virus_scan_errors_to_auditlog(virus_scan_errors, None, CityFurnitureDeviceTypeIcon, None)
                raise ValidationError(_(f"Virus scan failure: {get_error_details_message(virus_scan_errors)}"))
        return cleaned_data

    def save(self, commit=True):
        file = self.cleaned_data.get("file")
        if file and self.has_changed() and "file" in self.changed_data:
            pass

        return super().save(commit=commit)


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

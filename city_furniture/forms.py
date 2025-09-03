from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import ModelChoiceIteratorValue
from django.utils.translation import gettext_lazy as _

from city_furniture.models import CityFurnitureDeviceType, FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureDeviceTypeIcon
from traffic_control.admin.utils import ResponsibleEntityPermissionAdminFormMixin
from traffic_control.forms import Geometry3DFieldForm, SRIDBoundGeometryFormMixin
from traffic_control.services.virus_scan import add_virus_scan_errors_to_auditlog, get_error_details_message
from traffic_control.utils import get_icon_upload_obstacles


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

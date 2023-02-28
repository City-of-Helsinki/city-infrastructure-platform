import json

from django.views.generic import TemplateView

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models.common import TrafficControlDeviceType


class DeviceCatalog(TemplateView):
    target_model: DeviceTypeTargetModel

    def get_device_types(self, target_model: DeviceTypeTargetModel):
        device_types = TrafficControlDeviceType.objects.filter(target_model=target_model).order_by("code")

        # Prettify content schema JSON
        for dt in device_types:
            dt.content_schema = json.dumps(dt.content_schema, indent=4)

        return device_types

    def get_context_data(self, **kwargs):
        parent_context = super().get_context_data(**kwargs)

        return {
            **parent_context,
            "title": self.title,
            "device_types": self.get_device_types(self.target_model),
        }


class TrafficSignCatalog(DeviceCatalog):
    template_name = "catalogs/traffic_sign_catalog.html"
    title = "Traffic signs"
    target_model = DeviceTypeTargetModel.TRAFFIC_SIGN


class AdditionalSignCatalog(DeviceCatalog):
    template_name = "catalogs/additional_sign_catalog.html"
    title = "Additional signs"
    target_model = DeviceTypeTargetModel.ADDITIONAL_SIGN

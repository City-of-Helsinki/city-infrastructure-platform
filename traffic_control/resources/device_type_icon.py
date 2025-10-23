from import_export.resources import ModelResource

from traffic_control.models import TrafficControlDeviceTypeIcon


class TrafficControlDeviceTypeIconResource(ModelResource):
    class Meta:
        model = TrafficControlDeviceTypeIcon
        fields = ("file",)
        import_id_fields = ("file",)
        export_order = ("file",)
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

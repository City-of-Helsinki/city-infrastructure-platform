from os.path import splitext

from django.conf import settings

from traffic_control.models import Owner
from traffic_control.services.virus_scan import clam_av_scan


def get_default_owner():
    owner, _ = Owner.objects.get_or_create(
        name_fi="Helsingin kaupunki",
        name_en="City of Helsinki",
    )
    return owner


def get_allowed_file_upload_types():
    return settings.ALLOWED_FILE_UPLOAD_TYPES


def get_illegal_file_types(files):
    illegal_types = set()
    for _, file_ext in map(lambda x: splitext(x), files):
        if file_ext not in get_allowed_file_upload_types():
            illegal_types.add(file_ext)
    return illegal_types


def get_file_upload_obstacles(files):
    illegal_types = get_illegal_file_types([f.name for _, f in filter(lambda x: hasattr(x[1], "name"), files.items())])
    virus_scan_errors = clam_av_scan([("FILES", v) for _, v in files.items()])["errors"]
    return illegal_types, virus_scan_errors

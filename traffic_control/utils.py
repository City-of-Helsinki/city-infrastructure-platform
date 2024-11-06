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


def get_client_ip(request):
    """Function to get actual client ip if found from request headers"""
    if not (x_forwarded_for := request.headers.get("x-forwarded-for")):
        return request.META.get("REMOTE_ADDR")

    remote_addr = x_forwarded_for.split(",")[0]

    # Remove port number from remote_addr
    if "." in remote_addr and ":" in remote_addr:
        # IPv4 with port (`x.x.x.x:x`)
        remote_addr = remote_addr.split(":")[0]
    elif "[" in remote_addr:
        # IPv6 with port (`[:::]:x`)
        remote_addr = remote_addr[1:].split("]")[0]

    return remote_addr

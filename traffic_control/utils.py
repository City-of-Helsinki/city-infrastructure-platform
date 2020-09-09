from traffic_control.models import Owner


def get_default_owner():
    owner, _ = Owner.objects.get_or_create(
        name_fi="Helsingin kaupunki",
        name_en="City of Helsinki",
    )
    return owner

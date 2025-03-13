import uuid

from django.db import models


class ParkingZoneUpdateInfo(models.Model):
    """Just a small informative db table to track changes done when programmatically updating
    AdditionalSignReal.additional_information"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    update_infos = models.JSONField(blank=False, null=True)
    update_errors = models.JSONField(blank=False, null=True)
    database_update = models.BooleanField(default=False)

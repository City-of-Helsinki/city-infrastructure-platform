from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """Provides convenient methods for soft deletable QuerySet"""

    def active(self):
        return self.filter(is_active=True)

    def deleted(self):
        return self.filter(is_active=False)

    def soft_delete(self, user):
        """Django does not emit any signals when doing update or any bulk operation.
        LogEntries need to be manually created, instead call save on each object separately.
        As this kinda of operation is kinda rare on multititudes, this is now done by saving each object separately.
        if performance becomes an issue, calculating differeces and bulk create auditlog entries needs to be
        done manually.
        """
        deleted_at = timezone.now()
        for obj in self:
            obj.is_active = False
            obj.deleted_at = deleted_at
            obj.deleted_by = user
            obj.save(update_fields=["is_active", "deleted_at", "deleted_by"])


def order_queryset_by_z_coord_desc(queryset, geometry_field="location"):
    """Order an queryset based on point geometry's z coordinate"""
    return queryset.annotate(
        z_coord=models.ExpressionWrapper(
            models.Func(geometry_field, function="ST_Z"),
            output_field=models.FloatField(),
        )
    ).order_by("-z_coord")

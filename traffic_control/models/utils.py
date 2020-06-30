from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """Provides convenient methods for soft deletable QuerySet"""

    def active(self):
        return self.filter(is_active=True)

    def deleted(self):
        return self.filter(is_active=False)

    def soft_delete(self, user):
        self.update(is_active=False, deleted_at=timezone.now(), deleted_by=user)


def order_queryset_by_z_coord_desc(queryset, geometry_field="location"):
    """Order an queryset based on point geometry's z coordinate"""
    return queryset.annotate(
        z_coord=models.ExpressionWrapper(
            models.Func(geometry_field, function="ST_Z"),
            output_field=models.FloatField(),
        )
    ).order_by("-z_coord")

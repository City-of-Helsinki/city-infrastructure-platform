from django.db import models


class SoftDeleteQuerySet(models.QuerySet):
    """Provides convenient methods for soft deletable QuerySet"""

    def active(self):
        return self.filter(is_active=True)

    def deleted(self):
        return self.filter(is_active=False)


def order_queryset_by_z_coord_desc(queryset, geometry_field="location"):
    """Order an queryset based on point geometry's z coordinate"""
    return queryset.annotate(
        z_coord=models.ExpressionWrapper(
            models.Func(geometry_field, function="ST_Z"),
            output_field=models.FloatField(),
        )
    ).order_by("-z_coord")

from django.db import models


class SoftDeleteQuerySet(models.QuerySet):
    """Provides convenient methods for soft deletable QuerySet"""

    def active(self):
        return self.filter(is_active=True)

    def deleted(self):
        return self.filter(is_active=False)

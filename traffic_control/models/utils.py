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

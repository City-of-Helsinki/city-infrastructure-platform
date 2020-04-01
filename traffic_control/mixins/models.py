from django.utils import timezone


class SoftDeleteModelMixin:
    def soft_delete(self, user):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()

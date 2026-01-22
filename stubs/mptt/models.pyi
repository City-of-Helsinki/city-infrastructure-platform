from django.db import models
from mptt.managers import TreeManager

class MPTTModel(models.Model):
    objects: TreeManager

    class Meta:
        abstract = True

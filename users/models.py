import uuid

from django.contrib.gis.db import models
from helusers.models import AbstractUser


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)

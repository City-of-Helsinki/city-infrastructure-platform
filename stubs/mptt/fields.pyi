from django.db import models

class TreeForeignKey(models.ForeignKey[models.Model, models.Model | None]):
    pass

import uuid

from auditlog.registry import auditlog
from django.contrib.auth.models import Group
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from enumfields import EnumIntegerField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from traffic_control.enums import OrganizationLevel


class ResponsibleEntity(MPTTModel): # type: ignore[misc]
    """
    Responsible Entity for a City Furniture Device

    Organization chain is most often the following:
    Toimiala > Palvelu > Yksikkö > Projekti
    e.g.
    KYMP > Yleiset Alueet > Tiimi X > ABC123
    """

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name = models.CharField(_("Name"), max_length=254)
    external_id = models.CharField(
        _("External ID"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Use Projectwise ID for projects, can also be an abbreviation if entity has no ID"),
    )
    organization_level = EnumIntegerField(
        OrganizationLevel,
        verbose_name=_("Organization level"),
        default=OrganizationLevel.PROJECT,
        help_text=_("Describes the level of organization this is."),
    )
    parent = TreeForeignKey(
        "self",
        related_name="children",
        verbose_name=_("Parent Responsible Entity"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_(
            "Organization under which this object belongs to. "
            "This objects organizational level must be lower than its parents."
        ),
    )

    class Meta:
        verbose_name = _("Responsible Entity")
        verbose_name_plural = _("Responsible Entities")

    def get_full_path(self):
        ancestors = self.get_ancestors(include_self=True)
        return " > ".join([ancestor.name for ancestor in ancestors])

    def clean_parent(self):
        if self.parent and self.parent.organization_level.value > self.organization_level.value:
            raise ValidationError({"parent": "Parent's organization level can't be below this object's level."})

    def clean_fields(self, exclude=None):
        super(ResponsibleEntity, self).clean_fields()
        self.clean_parent()

    def __str__(self):
        return self.get_full_path()


class GroupResponsibleEntity(models.Model):
    """Model to link ResponsibleEntities to django.contrib.auth.Group model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.OneToOneField(
        Group,
        unique=True,
        related_name="group_responsible_entity",
        verbose_name=_("Group"),
        on_delete=models.CASCADE,
    )
    responsible_entities = models.ManyToManyField(
        "ResponsibleEntity",
        related_name="groups",
        verbose_name=_("Responsible Entities"),
        blank=True,
    )

    class Meta:
        verbose_name = _("Group responsible entity")
        verbose_name_plural = _("Group responsible entities")

    def __str__(self):
        return f"GroupResponsibleEntity {self.group.name}"


auditlog.register(ResponsibleEntity)
auditlog.register(GroupResponsibleEntity)

from django import forms
from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from city_furniture.models import ResponsibleEntity
from city_furniture.models.responsible_entity import GroupResponsibleEntity
from traffic_control.admin import AuditLogHistoryAdmin


class ResponsibleEntityAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parent_choices = ((re.id, re) for re in ResponsibleEntity.objects.exclude(id=self.instance.id))
        self.fields["parent"].choices = (("", "---"), *parent_choices)


@admin.register(ResponsibleEntity)
class ResponsibleEntityAdmin(AuditLogHistoryAdmin):
    list_display = (
        "id",
        "name",
        "organization_level",
        "parent",
    )
    ordering = ("organization_level",)
    actions = None
    form = ResponsibleEntityAdminForm


class GroupResponsibleEntityInline(admin.StackedInline):
    model = GroupResponsibleEntity
    can_delete = False
    verbose_name_plural = _("Responsible entities")
    filter_horizontal = ("responsible_entities",)

from django import forms
from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from traffic_control.admin import AuditLogHistoryAdmin
from traffic_control.models import GroupResponsibleEntity, ResponsibleEntity


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
    list_select_related = ("parent",)
    search_fields = ("id",)
    ordering = ("organization_level",)
    actions = None
    form = ResponsibleEntityAdminForm


class GroupResponsibleEntityInline(admin.StackedInline):
    model = GroupResponsibleEntity
    can_delete = False
    verbose_name_plural = _("Responsible entities")
    filter_horizontal = ("responsible_entities",)

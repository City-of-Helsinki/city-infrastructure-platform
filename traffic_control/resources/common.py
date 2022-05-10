from uuid import UUID

from django.core.exceptions import ValidationError
from django.db.models import NOT_PROVIDED
from django.utils.encoding import force_str
from import_export import fields, widgets
from import_export.admin import ImportExportActionModelAdmin
from import_export.formats import base_formats
from import_export.resources import ModelResource

from traffic_control.models import ResponsibleEntity
from users.models import User
from users.utils import get_system_user


class EnumIntegerWidget(widgets.Widget):
    def clean(self, value, row=None, *args, **kwargs):
        return value

    def render(self, value, obj=None):
        return force_str(value.name)


class ResourceEnumIntegerField(fields.Field):
    def __init__(
        self,
        attribute=None,
        column_name=None,
        enum=None,
        default=NOT_PROVIDED,
        readonly=False,
        saves_null_values=True,
    ):
        if enum is None:
            raise TypeError
        self.enum = enum
        super().__init__(attribute, column_name, EnumIntegerWidget(), default, readonly, saves_null_values)

    def clean(self, data, **kwargs):
        name = data[self.column_name]
        try:
            enum_value = self.enum.__getattr__(name)
        except AttributeError:
            if name in self.empty_values and self.default != NOT_PROVIDED:
                if callable(self.default):
                    enum_value = self.default()
                else:
                    enum_value = self.default
            else:
                raise KeyError(
                    "Key '%s' not found in enum. Available keys are: %s"
                    % (self.column_name, [e.name for e in self.enum])
                )

        data[self.column_name] = enum_value
        return super().clean(data, **kwargs)


class ResourceUUIDField(fields.Field):
    def get_value(self, obj):
        """Convert UUID to string to prevent the importer from thinking the value is changed, when it's not"""

        value = super().get_value(obj)
        if type(value) == UUID:
            value = str(value)
        return value


class GenericDeviceBaseResource(ModelResource):
    id = ResourceUUIDField(attribute="id", column_name="id", default=None)

    def get_queryset(self):
        return self._meta.model.objects.active()

    def after_import_instance(self, instance, new, row_number=None, **kwargs):
        """Set created_by and updated_by users"""
        user = kwargs.pop("user", None)
        if user is None:
            user = get_system_user()

        instance.updated_by = user
        if new:
            instance.created_by = user

        super().after_import_instance(instance, new, row_number=None, **kwargs)

    class Meta:
        skip_unchanged = True
        report_skipped = True

    def __str__(self):
        return self.__class__.__name__


class ResponsibleEntityPermissionImportMixin:
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        super().before_import(dataset, using_transactions, dry_run, **kwargs)
        user: User = kwargs.pop("user", None)

        if user is None:
            return

        if user.is_superuser or user.bypass_responsible_entity:
            return

        for row in dataset.dict:
            responsible_entity_name = row.get("responsible_entity__name")

            if responsible_entity_name is None or responsible_entity_name == "":
                raise ValidationError("You do not have permissions to create devices without a Responsible Entity set.")

            responsible_entity = ResponsibleEntity.objects.filter(name=responsible_entity_name).first()
            if responsible_entity is not None:
                if not user.has_responsible_entity_permission(responsible_entity):
                    raise ValidationError(
                        "You do not have permissions to create or modify devices with given "
                        f"Responsible Entity ({responsible_entity})"
                    )


class CustomImportExportActionModelAdmin(ImportExportActionModelAdmin):
    # Set CSV and XLSX as the only available formats
    formats = [f for f in base_formats.DEFAULT_FORMATS if f.__name__ in ["CSV", "XLSX"]]

from uuid import UUID

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.urls import path
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField, EnumIntegerField
from import_export import fields, widgets
from import_export.admin import ImportExportActionModelAdmin
from import_export.formats import base_formats
from import_export.resources import ModelResource

from traffic_control.models import ResponsibleEntity
from users.models import User
from users.utils import get_system_user


class EnumWidget(widgets.Widget):
    def __init__(self, enum=None):
        self.enum = enum

    def clean(self, value, row=None, *args, **kwargs):
        if value in [None, ""]:
            return None
        try:
            return self.enum[value]
        except KeyError:
            enum_values = ", ".join([e.name for e in self.enum])
            message = _(
                "Value '%(value)s' is invalid. Valid values are %(enum_values)s (%(enum)s)."
                % {"value": value, "enum": self.enum, "enum_values": enum_values}
            )
            raise ValueError(message)

    def render(self, value, obj=None):
        return force_str(value.name)


class ResourceUUIDField(fields.Field):
    def get_value(self, obj):
        """Convert UUID to string to prevent the importer from thinking the value is changed, when it's not"""

        value = super().get_value(obj)
        if type(value) == UUID:
            value = str(value)
        return value


class GenericDeviceBaseResource(ModelResource):
    id = ResourceUUIDField(attribute="id", column_name="id", default=None)

    @classmethod
    def field_from_django_field(cls, field_name, django_field, readonly):
        """
        In case Django model field is an enum field, set resource widget accordingly.
        Otherwise do ModelResource default behavior.
        """
        if type(django_field) in (EnumField, EnumIntegerField):
            field = cls.DEFAULT_RESOURCE_FIELD(
                attribute=field_name,
                column_name=field_name,
                widget=EnumWidget(django_field.enum),
                readonly=readonly,
                default=django_field.default,
            )
            return field
        else:
            return super().field_from_django_field(field_name, django_field, readonly)

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
        exclude = (
            "is_active",
            "deleted_at",
            "deleted_by",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        )

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

    def get_empty_csv_template(self, request):
        """Return a csv file, which contains only column names"""

        file_format = self.get_export_formats()[0]()  # Force CSV Format
        queryset = self.model.objects.none()
        export_data = self.get_export_data(file_format, queryset, request=request, encoding=self.to_encoding)

        response = HttpResponse(export_data, content_type=file_format.get_content_type())
        response["Content-Disposition"] = 'attachment; filename="%s"' % (
            f"{self.model.__name__}-Template.{file_format.get_extension()}"
        )
        return response

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("export_empty/", self.get_empty_csv_template, name="%s_%s_export_empty" % self.get_model_info()),
        ]
        return my_urls + urls

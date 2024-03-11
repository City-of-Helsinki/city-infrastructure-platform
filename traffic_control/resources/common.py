from typing import Dict, List, Optional, OrderedDict, Set
from uuid import UUID, uuid4

from django.contrib import messages
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
from tablib import Dataset

from traffic_control.models import ResponsibleEntity
from traffic_control.models.utils import SoftDeleteQuerySet
from traffic_control.services.virus_scan import add_virus_scan_errors_to_auditlog, clam_av_scan
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


class EnumFieldResourceMixin:
    """Mixin for ModelResource classes where model has enum fields."""

    @classmethod
    def field_from_django_field(cls, field_name, django_field, readonly):
        """
        In case Django model field is an enum field, set resource widget accordingly.
        Otherwise do ModelResource default behavior.
        """
        if isinstance(django_field, (EnumField, EnumIntegerField)):
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


class UUIDWidget(widgets.Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if value in [None, ""]:
            return None
        if isinstance(value, UUID):
            return value
        try:
            return UUID(str(value))
        except ValueError:
            raise ValueError("Value '%s' is not a valid UUID." % value)


class ResourceUUIDField(fields.Field):
    def get_value(self, obj):
        """Convert UUID to string to prevent the importer from thinking the value is changed, when it's not"""

        value = super().get_value(obj)
        if isinstance(value, UUID):
            value = str(value)
        return value


class ReplacementWidget(widgets.ForeignKeyWidget):
    def render(self, value, obj=None):
        val = super().render(value, obj)
        if val:
            return str(val)
        else:
            return ""


class ReplacementField(fields.Field):
    def __init__(
        self,
        replace_method: Optional[callable] = None,
        unreplace_method: Optional[callable] = None,
        **kwargs,
    ):
        self.replace_method = replace_method
        self.unreplace_method = unreplace_method
        super().__init__(**kwargs)

    def save(self, obj, data, is_m2m=False, **kwargs):
        if not self.readonly:
            replaces_id = data.get("replaces")
            newer_replaced = obj._meta.model.objects.get(pk=replaces_id) if replaces_id else None
            if obj.replaces == newer_replaced:
                # No change
                return
            if newer_replaced:
                self.replace_method(old=newer_replaced, new=obj)
            else:
                self.unreplace_method(obj)


class GenericDeviceBaseResource(EnumFieldResourceMixin, ModelResource):
    id = ResourceUUIDField(attribute="id", column_name="id", default=None, widget=UUIDWidget())

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


class ParentChildReplacementImportMixin:
    """Mixing for replacing non-UUID id values with UUIDs in parent-child relations before import"""

    def before_import(self, dataset: Dataset, using_transactions, dry_run, **kwargs):
        super().before_import(dataset, using_transactions, dry_run, **kwargs)
        self._link_children_to_parents(dataset)

    def _link_children_to_parents(self, dataset: Dataset):
        id_header = self._meta.id_header
        parent_id_header = self._meta.parent_id_header

        # We cannot do linking if id and parent id are not present the import dataset
        if id_header not in dataset.headers or parent_id_header not in dataset.headers:
            return

        ids_column, replacements = self._get_id_column_and_replacements(dataset)
        parent_ids_column = self._get_replaced_parent_id_column(dataset, replacements)

        del dataset[id_header]
        dataset.append_col(col=ids_column, header=id_header)
        del dataset[parent_id_header]
        dataset.append_col(col=parent_ids_column, header=parent_id_header)

    def _get_id_column_and_replacements(self, dataset: Dataset):
        ids_column = []
        replacements = {}

        for row in dataset.dict:
            id_value = row[self._meta.id_header]
            if id_value in [None, ""]:
                ids_column.append(None)
            else:
                id_value = str(id_value)
                try:
                    # Try to interpret value as UUID
                    device_id = UUID(id_value)
                except ValueError:
                    # If value cannot be interpreted as UUID then id_value was a replacement value
                    device_id = uuid4()
                    replacements[id_value] = device_id
                ids_column.append(device_id)

        return ids_column, replacements

    def _get_replaced_parent_id_column(self, dataset: Dataset, replacements: Dict[str, UUID]):
        parent_ids_column = []

        for row in dataset.dict:
            parent_id_value = row[self._meta.parent_id_header]
            if parent_id_value in [None, ""]:
                parent_ids_column.append(None)
            else:
                parent_id_value = str(parent_id_value)
                try:
                    # Try to interpret value as UUID
                    parent_id = UUID(parent_id_value)
                except ValueError:
                    # If value cannot be interpreted as UUID then we find a replacement value, if available
                    parent_id = replacements.get(parent_id_value, parent_id_value)
                parent_ids_column.append(parent_id)

        return parent_ids_column

    class Meta:
        id_header = "id"
        parent_id_header = "parent__id"


class ParentChildReplacementPlanToRealExportMixin:
    """
    Mixin to replace real device ids and parent ids with replaceable (non-UUID) values after export.
    Any UUID references to existing real devices are retained.
    """

    def after_export(self, queryset: SoftDeleteQuerySet, data: Dataset, *args, **kwargs):
        super().after_export(queryset, data, *args, **kwargs)
        self._replace_ids_with_replaceable_values(queryset, data)

    def _replace_ids_with_replaceable_values(self, queryset: SoftDeleteQuerySet, dataset: Dataset):
        id_header = self._meta.id_header
        parent_id_header = self._meta.parent_id_header
        real_model_plan_id_field = self._meta.real_model_plan_id_field

        plan_ids = list(queryset.values_list("id", flat=True))
        plan_parent_ids = list(queryset.values_list("parent", flat=True))
        plan_parent_ids_distinct = list(queryset.exclude(parent=None).values_list("parent", flat=True).distinct())

        # Exclude plan ids which have existing reals
        plan_ids_with_existing_reals = list(
            self._meta.real_model.objects.filter(
                **{f"{real_model_plan_id_field}__in": plan_parent_ids_distinct}
            ).values_list(real_model_plan_id_field, flat=True)
        )
        plan_parent_ids_distinct = list(set(plan_parent_ids_distinct) - set(plan_ids_with_existing_reals))

        ids_column = dataset[id_header]
        parent_ids_column = dataset[parent_id_header]

        # Assume that queryset elements match with dataset rows
        for row_index, row in enumerate(dataset.dict):
            # Replace id
            try:
                ids_column[row_index] = plan_parent_ids_distinct.index(plan_ids[row_index]) + 1
            except ValueError:
                pass
            # Replace parent id
            try:
                parent_ids_column[row_index] = plan_parent_ids_distinct.index(plan_parent_ids[row_index]) + 1
            except ValueError:
                pass

        # Replace columns in the dataset
        del dataset[id_header]
        dataset.insert_col(0, ids_column, id_header)
        del dataset[parent_id_header]
        dataset.insert_col(1, parent_ids_column, parent_id_header)

        # Sort dataset so that parent objects are always before their children
        self._sort_dataset(dataset, queryset)

    def _sort_dataset(self, data: Dataset, queryset):
        # Copy dataset so that we can edit the original in-place
        original_data = Dataset(headers=data.headers, title=data.title)
        for item in data.dict:
            row = [item[key] for key in data.headers]
            original_data.append(row=row)

        # Wipe data and add rows back in sorted order
        ordered_plan_ids = self._get_parent_child_id_order(queryset)
        data.wipe()
        data.headers = original_data.headers
        data.title = original_data.title
        sorted_dict = sorted(original_data.dict, key=lambda x: ordered_plan_ids.index(x[self._meta.plan_id_header]))
        for item in sorted_dict:
            row = [item[key] for key in data.headers]
            data.append(row=row)

    def _get_parent_child_id_order(
        self,
        queryset: SoftDeleteQuerySet,
        parent_id: Optional[UUID] = None,
        parent_child_id_order: Optional[List[UUID]] = None,
    ) -> List[UUID]:
        """Recursively build a list of ids in the order where parents are before their children."""

        if parent_child_id_order is None:
            parent_child_id_order = []

        children_qs = queryset.filter(parent_id=parent_id)
        # In the first recursive iteration we also must include orphaned devices
        if parent_id is None:
            children_qs = children_qs.union(queryset.filter(id__in=self._get_orphaned_devices(queryset)))

        for child in children_qs.values_list("id", "parent_id", named=True):
            parent_child_id_order.append(child.id)
            self._get_parent_child_id_order(queryset, parent_id=child.id, parent_child_id_order=parent_child_id_order)
        return parent_child_id_order

    @staticmethod
    def _get_orphaned_devices(queryset: SoftDeleteQuerySet) -> Set[UUID]:
        """Returns devices which parents are not in the `queryset`."""

        orphaned = set()
        ids = set(queryset.values_list("id", flat=True))
        for id, parent_id in queryset.values_list("id", "parent_id"):
            if parent_id is not None and parent_id not in ids:
                orphaned.add(id)
        return orphaned

    class Meta:
        id_header = "id"
        parent_id_header = "parent__id"


class ResponsibleEntityPermissionImportMixin:
    def before_import(self, dataset: Dataset, using_transactions: bool, dry_run: bool, **kwargs):
        super().before_import(dataset, using_transactions, dry_run, **kwargs)
        user: User = kwargs.pop("user", None)

        if user is None:
            return

        if user.is_superuser or user.bypass_responsible_entity:
            return

        for row in dataset.dict:
            # If device already exists, check that user has permission to modify it
            self._validate_device_current_responsible_entity_permission(row, user)

            # Check permissions for target responsible entity (create or update)
            self._validate_device_target_responsible_entity_permission(row, user)

    def _validate_device_current_responsible_entity_permission(self, row: OrderedDict, user: User):
        device_id = row.get("id")
        if not device_id:
            # There's no current device
            return

        device = self._meta.model.objects.filter(id=device_id).first()
        if not device:
            # Device with the ID does not exist yet
            return

        responsible_entity = device.responsible_entity
        if not responsible_entity:
            raise ValidationError(_("You do not have a permission to modify devices without a responsible entity."))

        if not user.has_responsible_entity_permission(responsible_entity):
            raise ValidationError(
                _("You do not have a permission to modify devices of responsible entity '%(responsible_entity)s'."),
                params={"responsible_entity": responsible_entity},
            )

    @staticmethod
    def _validate_device_target_responsible_entity_permission(row: OrderedDict, user: User):
        responsible_entity_name = row.get("responsible_entity__name")
        if responsible_entity_name in (None, ""):
            raise ValidationError(
                _(
                    "You do not have a permission to create devices without a responsible entity "
                    "or to remove responsible entity from existing devices."
                )
            )

        responsible_entity = ResponsibleEntity.objects.filter(name=responsible_entity_name).first()
        if responsible_entity:
            if not user.has_responsible_entity_permission(responsible_entity):
                raise ValidationError(
                    _(
                        "You do not have a permission to create or modify devices with given "
                        "responsible entity (%(responsible_entity)s)."
                    ),
                    params={"responsible_entity": responsible_entity},
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

    def import_action(self, request, *args, **kwargs):
        """Add virus scan to before actual import"""
        if request.FILES:
            scan_response = clam_av_scan([("FILES", v) for _, v in request.FILES.items()])
            errors = scan_response["errors"]
            if errors:
                add_virus_scan_errors_to_auditlog(errors, request.user, self.model, object_id=None)
                self.message_user(request, errors, messages.ERROR)
                del request.FILES["import_file"]

        return super().import_action(request, *args, **kwargs)

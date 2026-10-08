"""Support for importing attachment files together with device data in the admin import.

Attachment files are uploaded on the admin import page and referenced by name from a column in the
imported data file. Two mixins make up the feature:

* :class:`AttachmentImportAdminMixin` stages the uploaded files and carries the batch over the
  two step admin import.
* :class:`AttachmentImportMixin` validates the referenced file names and attaches the staged files
  to the imported devices. It also renders the resulting file names in the import preview through
  :class:`AttachmentDiff`.

Adopting the feature for a new model requires adding both mixins and declaring the attachment
settings in the resource's ``Meta``::

    class MyDeviceResource(AttachmentImportMixin, GenericDeviceBaseResource):
        class Meta(GenericDeviceBaseResource.Meta):
            model = MyDevice
            attachment_model = MyDeviceFile
            attachment_fk_field = "my_device"
            fields = (..., ATTACHMENT_COLUMN_NAME)
"""

import logging
import os
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Type

from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models
from django.utils.translation import gettext_lazy as _
from import_export import fields
from import_export.resources import Diff

from traffic_control.resources.forms import AttachmentConfirmImportForm, AttachmentImportForm
from traffic_control.services.import_attachments import (
    AttachmentStagingError,
    discard_batch,
    list_staged,
    open_staged,
    sanitize_filename,
)

logger = logging.getLogger(__name__)

ATTACHMENT_COLUMN_NAME = "attachment_filenames"
ATTACHMENT_FILENAME_SEPARATOR = ";"

#: Instance attribute carrying the attachment file names a row results in, set during an import
#: so that the import preview can show them before they are written.
PREVIEW_FILENAMES_ATTRIBUTE = "_preview_attachment_filenames"


def parse_attachment_filenames(value: Any) -> List[str]:
    """Parse the attachment file name column value into a list of file names.

    Args:
        value (Any): Raw cell value of the attachment file name column.

    Returns:
        List[str]: Sanitized file names in the order they were listed, without duplicates.
    """
    if not value:
        return []

    names = []
    for raw_name in str(value).split(ATTACHMENT_FILENAME_SEPARATOR):
        name = raw_name.strip()
        if name and name not in names:
            names.append(sanitize_filename(name))
    return names


class AttachmentDiff(Diff):
    """Import preview diff that renders the attachment column through its dehydrate method.

    ``import_export.resources.Diff`` reads field values with ``Field.export()``, which bypasses
    the resource's ``dehydrate_<field>`` methods. The attachment file name field has no model
    attribute, so without this class its preview column is always empty. Other fields are read
    exactly like the base class does.

    ``Diff`` calls ``Diff._read_field_values()`` by its hardcoded class name, so both value
    reading methods have to be overridden instead of just that one.
    """

    def __init__(self, resource: Any, instance: Optional[models.Model], new: bool) -> None:
        super().__init__(resource, instance, new)
        self.left = self._read_values(resource, instance)

    def compare_with(self, resource: Any, instance: Optional[models.Model]) -> None:
        """Read the values shown as the new state of the row in the import preview.

        Args:
            resource (Any): Resource the import is run with.
            instance (Optional[models.Model]): Imported device, ``None`` for deleted rows.

        Returns:
            None
        """
        self.right = self._read_values(resource, instance)

    @staticmethod
    def _read_values(resource: Any, instance: Optional[models.Model]) -> List[Any]:
        """Read the values of one side of the import preview.

        Args:
            resource (Any): Resource the import is run with.
            instance (Optional[models.Model]): Device to read the values from.

        Returns:
            List[Any]: Exported value of every import field.
        """
        values = []
        for field in resource.get_import_fields():
            if field.column_name == ATTACHMENT_COLUMN_NAME:
                values.append(resource.export_field(field, instance))
            else:
                values.append(field.export(instance))
        return values


class AttachmentApplyStrategy:
    """Base strategy deciding how imported attachment files are applied to a device."""

    def apply(
        self,
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
        filenames: Sequence[str],
        batch_id: str,
    ) -> None:
        """Apply the listed attachment files to the given device instance.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.
            filenames (Sequence[str]): Names of the staged files to attach.
            batch_id (str): Identifier of the staged attachment batch.

        Returns:
            None

        Raises:
            NotImplementedError: Always, subclasses must implement this.
        """
        raise NotImplementedError

    def preview_names(
        self,
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
        filenames: Sequence[str],
    ) -> List[str]:
        """Return the file names the device ends up with when the listed files are applied.

        Used to render the import preview, where the attachments have not been written yet.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.
            filenames (Sequence[str]): Names of the files listed by the imported row.

        Returns:
            List[str]: Names of the device's attachments after the import.

        Raises:
            NotImplementedError: Always, subclasses must implement this.
        """
        raise NotImplementedError

    @classmethod
    def _existing_names(
        cls,
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
    ) -> List[str]:
        """Return the file names of a device's existing attachments.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.

        Returns:
            List[str]: Base names of the device's current attachment files.
        """
        if instance.pk is None:
            return []

        queryset = cls._existing_queryset(instance, attachment_model, fk_field)
        return [os.path.basename(name) for name in queryset.order_by("file").values_list("file", flat=True)]

    @staticmethod
    def _existing_queryset(
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
    ) -> models.QuerySet:
        """Return the existing attachments of a device.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.

        Returns:
            models.QuerySet: Existing attachment rows of the device.
        """
        return attachment_model.objects.filter(**{fk_field: instance})

    @staticmethod
    def _create_attachments(
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
        filenames: Sequence[str],
        batch_id: str,
    ) -> None:
        """Create attachment rows for the given staged file names.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.
            filenames (Sequence[str]): Names of the staged files to attach.
            batch_id (str): Identifier of the staged attachment batch.

        Returns:
            None
        """
        staged = list_staged(batch_id)
        for filename in filenames:
            if filename not in staged:
                # Already attached to the device, or not uploaded at all: nothing to create.
                continue
            with open_staged(batch_id, filename) as staged_file:
                attachment = attachment_model(**{fk_field: instance})
                attachment.file.save(filename, File(staged_file, name=filename), save=False)
                attachment.save()


class ReplaceAttachmentsStrategy(AttachmentApplyStrategy):
    """Make the device's attachments match the listed file names exactly.

    The listed names are the device's desired final set of attachments: names the device already
    has an attachment for are kept as they are, names found in the staged upload batch are added
    and existing attachments that are not listed are deleted.

    Only ever invoked for rows that actually list attachment file names, so a row with an empty
    attachment column keeps its existing attachments.
    """

    def apply(
        self,
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
        filenames: Sequence[str],
        batch_id: str,
    ) -> None:
        """Make the device's attachments match the listed files.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.
            filenames (Sequence[str]): Names of the files the device should end up with.
            batch_id (str): Identifier of the staged attachment batch.

        Returns:
            None
        """
        listed = set(filenames)
        kept_names = set()

        for existing in self._existing_queryset(instance, attachment_model, fk_field):
            name = os.path.basename(existing.file.name)
            if name in listed:
                kept_names.add(name)
                continue
            existing.delete()

        new_filenames = [name for name in filenames if name not in kept_names]
        self._create_attachments(instance, attachment_model, fk_field, new_filenames, batch_id)

    def preview_names(
        self,
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
        filenames: Sequence[str],
    ) -> List[str]:
        """Return the listed file names, which become the device's whole attachment set.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.
            filenames (Sequence[str]): Names of the files listed by the imported row.

        Returns:
            List[str]: Names of the device's attachments after the import.
        """
        return list(filenames)


class AppendAttachmentsStrategy(AttachmentApplyStrategy):
    """Keep the device's existing attachments and add the imported ones."""

    def apply(
        self,
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
        filenames: Sequence[str],
        batch_id: str,
    ) -> None:
        """Add the listed files to the device's existing attachments.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.
            filenames (Sequence[str]): Names of the staged files to attach.
            batch_id (str): Identifier of the staged attachment batch.

        Returns:
            None
        """
        self._create_attachments(instance, attachment_model, fk_field, filenames, batch_id)

    def preview_names(
        self,
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
        filenames: Sequence[str],
    ) -> List[str]:
        """Return the device's existing file names followed by the listed ones.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.
            filenames (Sequence[str]): Names of the files listed by the imported row.

        Returns:
            List[str]: Names of the device's attachments after the import.
        """
        return self._existing_names(instance, attachment_model, fk_field) + list(filenames)


class AppendSkipExistingAttachmentsStrategy(AttachmentApplyStrategy):
    """Add the imported files, skipping names the device already has an attachment for."""

    def apply(
        self,
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
        filenames: Sequence[str],
        batch_id: str,
    ) -> None:
        """Add the listed files that the device does not already have.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.
            filenames (Sequence[str]): Names of the staged files to attach.
            batch_id (str): Identifier of the staged attachment batch.

        Returns:
            None
        """
        existing_names = {
            os.path.basename(existing.file.name)
            for existing in self._existing_queryset(instance, attachment_model, fk_field)
        }
        new_filenames = [name for name in filenames if name not in existing_names]
        self._create_attachments(instance, attachment_model, fk_field, new_filenames, batch_id)

    def preview_names(
        self,
        instance: models.Model,
        attachment_model: Type[models.Model],
        fk_field: str,
        filenames: Sequence[str],
    ) -> List[str]:
        """Return the device's existing file names plus the listed ones it does not have yet.

        Args:
            instance (models.Model): Device the attachments belong to.
            attachment_model (Type[models.Model]): Model storing the attachment files.
            fk_field (str): Name of the foreign key field pointing back to the device.
            filenames (Sequence[str]): Names of the files listed by the imported row.

        Returns:
            List[str]: Names of the device's attachments after the import.
        """
        existing_names = self._existing_names(instance, attachment_model, fk_field)
        return existing_names + [name for name in filenames if name not in existing_names]


class AttachmentImportMixin:
    """Resource mixin attaching uploaded files to imported devices.

    The mixin is a no-op when no attachment files were uploaded and the attachment column is empty,
    so resources using it keep working for plain data-only imports.
    """

    #: Declared as an ``OrderedDict`` rather than a class attribute because the import-export
    #: declarative metaclass only collects fields from bases that expose a ``fields`` mapping.
    fields = OrderedDict(
        [
            (
                ATTACHMENT_COLUMN_NAME,
                fields.Field(column_name=ATTACHMENT_COLUMN_NAME, attribute=None),
            )
        ]
    )

    def __init__(self, attachment_batch_id: Optional[str] = None, **kwargs: Any) -> None:
        self.attachment_batch_id = attachment_batch_id or None
        super().__init__(**kwargs)

    def get_diff_class(self) -> Type[Diff]:
        """Return the diff class used to render the import preview.

        Returns:
            Type[Diff]: Diff class that renders fields through the resource's dehydrate methods.
        """
        return AttachmentDiff

    def get_attachment_strategy(self) -> AttachmentApplyStrategy:
        """Return the strategy used to apply attachments to a device.

        Returns:
            AttachmentApplyStrategy: Configured strategy instance.
        """
        strategy_class = getattr(self._meta, "attachment_strategy", None) or ReplaceAttachmentsStrategy
        return strategy_class()

    def dehydrate_attachment_filenames(self, obj: Optional[models.Model]) -> str:
        """Render the device's attachment file names for export and for the import preview.

        During an import the names the row would result in are used, as the attachments have not
        been written yet in a dry run.

        Args:
            obj (Optional[models.Model]): Device being exported.

        Returns:
            str: Separator joined file names, or an empty string when there are none.
        """
        previewed = getattr(obj, PREVIEW_FILENAMES_ATTRIBUTE, None) if obj is not None else None
        if previewed is not None:
            return ATTACHMENT_FILENAME_SEPARATOR.join(previewed)

        attachment_model = getattr(self._meta, "attachment_model", None)
        fk_field = getattr(self._meta, "attachment_fk_field", None)
        if obj is None or obj.pk is None or attachment_model is None or fk_field is None:
            return ""

        names = attachment_model.objects.filter(**{fk_field: obj}).order_by("file").values_list("file", flat=True)
        return ATTACHMENT_FILENAME_SEPARATOR.join(os.path.basename(name) for name in names)

    def before_import_row(self, row: Dict[str, Any], **kwargs: Any) -> None:
        """Validate that every attachment file referenced by the row has been uploaded.

        Args:
            row (Dict[str, Any]): Row data of the import file.
            **kwargs (Any): Import keyword arguments.

        Returns:
            None

        Raises:
            ValidationError: If the row references file names that were not uploaded.
        """
        super().before_import_row(row, **kwargs)

        filenames = self._get_row_filenames(row)
        if not filenames:
            return

        staged = list_staged(self.attachment_batch_id)
        already_attached = self._get_existing_attachment_names(row)
        missing = [name for name in filenames if name not in staged and name not in already_attached]
        if missing:
            raise ValidationError(
                {
                    ATTACHMENT_COLUMN_NAME: _("Attachment file(s) %(missing)s were not uploaded with this import.")
                    % {"missing": ", ".join(missing)}
                }
            )

    def skip_row(
        self,
        instance: models.Model,
        original: Optional[models.Model],
        row: Dict[str, Any],
        import_validation_errors: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Never skip a row that carries attachment file names.

        ``skip_unchanged`` is enabled for device resources, which would prevent attachments from
        being applied when only the attachments change.

        Args:
            instance (models.Model): New or updated device instance.
            original (Optional[models.Model]): Persisted device instance.
            row (Dict[str, Any]): Row data of the import file.
            import_validation_errors (Optional[Dict[str, Any]]): Validation errors found so far.

        Returns:
            bool: ``True`` if the row should be skipped.
        """
        if self._get_row_filenames(row):
            return False

        return super().skip_row(instance, original, row, import_validation_errors=import_validation_errors)

    def after_save_instance(self, instance: models.Model, row: Dict[str, Any], **kwargs: Any) -> None:
        """Attach the staged files listed by the row to the saved device.

        A row that does not list any attachment file names leaves the device's existing
        attachments untouched. Attachments are only ever modified for rows that explicitly list
        file names, so a data file without an attachment column never removes anything.

        The resulting file names are also stored on the instance for the import preview, which is
        rendered from a dry run where no attachment has been written yet.

        Args:
            instance (models.Model): The saved device instance.
            row (Dict[str, Any]): Row data of the import file.
            **kwargs (Any): Import keyword arguments.

        Returns:
            None
        """
        super().after_save_instance(instance, row, **kwargs)

        filenames = self._get_row_filenames(row)
        if not filenames:
            # No list given for this row: never touch the device's current attachments.
            return

        attachment_model, fk_field = self._get_attachment_config()
        if attachment_model is None or fk_field is None:
            logger.warning(
                "%s lists attachment files but has no attachment_model/attachment_fk_field configured",
                type(self).__name__,
            )
            return

        strategy = self.get_attachment_strategy()
        setattr(
            instance,
            PREVIEW_FILENAMES_ATTRIBUTE,
            strategy.preview_names(instance, attachment_model, fk_field, filenames),
        )

        if self._is_dry_run(kwargs):
            return

        strategy.apply(
            instance,
            attachment_model,
            fk_field,
            filenames,
            self.attachment_batch_id,
        )

    def _get_attachment_config(self) -> Tuple[Optional[Type[models.Model]], Optional[str]]:
        """Return the configured attachment model and foreign key field name.

        Returns:
            Tuple[Optional[Type[models.Model]], Optional[str]]: The attachment model and the name
            of its foreign key field pointing to the device.
        """
        return getattr(self._meta, "attachment_model", None), getattr(self._meta, "attachment_fk_field", None)

    def _get_row_instance_pk(self, row: Dict[str, Any]) -> Optional[Any]:
        """Return the primary key of the existing device a row refers to.

        Args:
            row (Dict[str, Any]): Row data of the import file.

        Returns:
            Optional[Any]: The device's primary key, or ``None`` for rows that create a new device.
        """
        id_fields = getattr(self._meta, "import_id_fields", None) or []
        if len(id_fields) != 1:
            return None

        value = row.get(id_fields[0])
        return value if value not in (None, "") else None

    def _get_existing_attachment_names(self, row: Dict[str, Any]) -> Set[str]:
        """Return the file names of the attachments the row's device already has.

        Args:
            row (Dict[str, Any]): Row data of the import file.

        Returns:
            Set[str]: Base names of the device's current attachment files, empty when the row
                creates a new device or the resource has no attachment model configured.
        """
        attachment_model, fk_field = self._get_attachment_config()
        instance_pk = self._get_row_instance_pk(row)
        if attachment_model is None or fk_field is None or instance_pk is None:
            return set()

        try:
            names = attachment_model.objects.filter(**{fk_field: instance_pk}).values_list("file", flat=True)
            return {os.path.basename(name) for name in names}
        except (ValueError, ValidationError):
            # An unparseable id is reported by the resource's own id field validation.
            return set()

    @staticmethod
    def _get_row_filenames(row: Dict[str, Any]) -> List[str]:
        """Return the attachment file names listed by a row.

        Args:
            row (Dict[str, Any]): Row data of the import file.

        Returns:
            List[str]: Sanitized attachment file names.

        Raises:
            ValidationError: If a listed file name is not a valid file name.
        """
        try:
            return parse_attachment_filenames(row.get(ATTACHMENT_COLUMN_NAME))
        except AttachmentStagingError as error:
            raise ValidationError({ATTACHMENT_COLUMN_NAME: str(error)})

    class Meta:
        attachment_model = None
        attachment_fk_field = None
        attachment_strategy = ReplaceAttachmentsStrategy


class AttachmentImportAdminMixin:
    """Admin mixin adding an attachment file upload to the import view.

    Must be mixed in before ``CustomImportExportActionModelAdmin``.
    """

    #: Adds the list of staged attachment files to the import confirmation page.
    import_template_name = "admin/import_export/attachment_import.html"

    def get_import_form_class(self, request: Any) -> type:
        """Return the import form class used for the first import step.

        Args:
            request (Any): The current request.

        Returns:
            type: Form class accepting attachment file uploads.
        """
        return AttachmentImportForm

    def create_import_form(self, request: Any) -> Any:
        """Create the import form and give it the context needed for virus scan audit logging.

        Args:
            request (Any): The current request.

        Returns:
            Any: The instantiated import form.
        """
        form = super().create_import_form(request)
        form.scan_user = request.user
        form.scan_model = self.model
        return form

    def get_confirm_form_class(self, request: Any) -> type:
        """Return the form class used for the import confirmation step.

        Args:
            request (Any): The current request.

        Returns:
            type: Form class carrying the staged attachment batch id.
        """
        return AttachmentConfirmImportForm

    def get_confirm_form_initial(self, request: Any, import_form: Any) -> Dict[str, Any]:
        """Add the staged attachment batch id to the confirm form's initial values.

        Args:
            request (Any): The current request.
            import_form (Any): The validated import form of the first step.

        Returns:
            Dict[str, Any]: Initial values for the confirm form.
        """
        initial = super().get_confirm_form_initial(request, import_form)
        if import_form is not None:
            initial["attachment_batch_id"] = import_form.cleaned_data.get("attachment_batch_id", "")
        return initial

    def get_import_resource_kwargs(self, request: Any, **kwargs: Any) -> Dict[str, Any]:
        """Pass the staged attachment batch id to the import resource.

        Args:
            request (Any): The current request.
            **kwargs (Any): Keyword arguments for the resource constructor.

        Returns:
            Dict[str, Any]: Keyword arguments including ``attachment_batch_id``.
        """
        resource_kwargs = super().get_import_resource_kwargs(request, **kwargs)
        form = kwargs.get("form")
        batch_id = getattr(form, "cleaned_data", {}).get("attachment_batch_id") if form else None
        resource_kwargs["attachment_batch_id"] = batch_id or None
        return resource_kwargs

    def process_import(self, request: Any, **kwargs: Any) -> Any:
        """Run the confirmed import and discard the staged attachment batch afterwards.

        Args:
            request (Any): The current request.
            **kwargs (Any): Keyword arguments passed on to the import.

        Returns:
            Any: The response of the import.
        """
        batch_id = request.POST.get("attachment_batch_id") or None
        try:
            return super().process_import(request, **kwargs)
        finally:
            discard_batch(batch_id)

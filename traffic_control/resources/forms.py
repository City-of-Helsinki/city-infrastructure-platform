"""Forms used by the admin import views that support uploading attachment files."""

import logging
from typing import Any, List, Optional

from django import forms
from django.utils.translation import gettext_lazy as _
from import_export.forms import ConfirmImportForm, ImportForm

from traffic_control.services.import_attachments import list_staged, stage_import_attachments

logger = logging.getLogger(__name__)


class MultipleFileInput(forms.ClearableFileInput):
    """File input widget that accepts multiple files and lists the selected file names."""

    allow_multiple_selected = True
    template_name = "traffic_control/widgets/multiple_file_input.html"

    class Media:
        css = {"all": ("traffic_control/css/import_attachment_files.css",)}
        js = ("traffic_control/js/import_attachment_files.js",)

    def get_context(self, name: str, value: Any, attrs: Optional[dict]) -> dict:
        """Add the translated labels used by the selected file list to the widget context.

        Args:
            name (str): Name of the form field.
            value (Any): Current value of the field.
            attrs (Optional[dict]): Extra HTML attributes for the input element.

        Returns:
            dict: Template context of the widget.
        """
        context = super().get_context(name, value, attrs)
        context["empty_text"] = _("No files selected")
        context["heading_text"] = _("Selected files")
        return context


class MultipleFileField(forms.FileField):
    """Form field that cleans every file of a multiple file upload."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data: Any, initial: Optional[Any] = None) -> List[Any]:
        """Clean each uploaded file individually.

        Args:
            data (Any): A single uploaded file or a list of uploaded files.
            initial (Optional[Any]): Initial value of the field.

        Returns:
            List[Any]: List of cleaned uploaded files.
        """
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(single, initial) for single in data]
        if data in self.empty_values:
            return []
        return [single_file_clean(data, initial)]


class AttachmentImportForm(ImportForm):
    """Import form that additionally accepts attachment files for the imported devices."""

    attachment_files = MultipleFileField(
        label=_("Attachment files"),
        required=False,
        help_text=_(
            "Optional files to attach to the imported devices. Reference the uploaded file names in the "
            "import file's attachment file name column. Separate multiple file names with a semicolon (;)."
        ),
    )

    #: Set by the admin so virus scan failures can be written to the audit log with context.
    scan_user: Any = None
    scan_model: Any = None

    def clean(self) -> dict:
        """Virus scan and stage the uploaded attachment files.

        Returns:
            dict: Cleaned form data including the ``attachment_batch_id`` of the staged files.
        """
        cleaned_data = super().clean()
        cleaned_data["attachment_batch_id"] = ""

        uploaded_files = cleaned_data.get("attachment_files") or []
        if not uploaded_files:
            return cleaned_data

        try:
            cleaned_data["attachment_batch_id"] = (
                stage_import_attachments(uploaded_files, user=self.scan_user, model=self.scan_model) or ""
            )
        except forms.ValidationError as error:
            self.add_error("attachment_files", error)

        return cleaned_data


class AttachmentConfirmImportForm(ConfirmImportForm):
    """Confirm form carrying the staged attachment batch over to the confirmation step."""

    attachment_batch_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Media:
        css = {"all": ("traffic_control/css/import_attachment_files.css",)}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._staged_attachment_names: Optional[List[str]] = None

    def get_attachment_batch_id(self) -> str:
        """Return the staged attachment batch id of this form.

        Returns:
            str: Batch identifier, or an empty string when no files were staged.
        """
        if self.is_bound:
            return self.data.get(self.add_prefix("attachment_batch_id")) or ""
        return self.initial.get("attachment_batch_id") or ""

    @property
    def staged_attachment_names(self) -> List[str]:
        """Return the names of the attachment files staged for this import.

        Returns:
            List[str]: Alphabetically sorted file names, empty when nothing is staged or the
                staging storage cannot be read.
        """
        if self._staged_attachment_names is None:
            self._staged_attachment_names = self._list_staged_attachment_names()
        return self._staged_attachment_names

    def _list_staged_attachment_names(self) -> List[str]:
        """Read the staged attachment file names from the staging storage.

        Returns:
            List[str]: Alphabetically sorted file names, empty when nothing is staged or the
                staging storage cannot be read.
        """
        batch_id = self.get_attachment_batch_id()
        if not batch_id:
            return []

        try:
            return sorted(list_staged(batch_id).keys())
        except Exception:
            logger.warning("Could not list staged import attachments for batch %s", batch_id, exc_info=True)
            return []

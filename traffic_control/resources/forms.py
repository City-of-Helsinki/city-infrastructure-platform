"""Forms used by the admin import views that support uploading attachment files."""

from typing import Any, List, Optional

from django import forms
from django.utils.translation import gettext_lazy as _
from import_export.forms import ConfirmImportForm, ImportForm

from traffic_control.services.import_attachments import stage_import_attachments


class MultipleFileInput(forms.ClearableFileInput):
    """File input widget that accepts multiple files."""

    allow_multiple_selected = True


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

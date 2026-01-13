from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.urls import reverse

from traffic_control.models import AdditionalSignPlan


class Command(BaseCommand):
    help = "Runs clean() on all AdditionalSignPlan objects to identify validation errors"

    def handle(self, *args, **options):
        additional_sign_plans = AdditionalSignPlan.objects.all()
        total_count = additional_sign_plans.count()
        error_count = 0

        BASE_URL = getattr(settings, "BASE_URL", "http://127.0.0.1:8000").rstrip("/")

        self.stdout.write(f"Starting validation for {total_count} AdditionalSignPlan objects...\n")

        for obj in additional_sign_plans:
            try:
                # This triggers all field, model-level, and unique validation
                obj.clean()
            except ValidationError as e:
                error_count += 1
                # Format the error dictionary for readability
                errors = ", ".join([f"{k}: {v}" for k, v in e.message_dict.items()])

                admin_path = reverse("admin:traffic_control_additionalsignplan_change", args=[obj.pk])
                full_url = f"{BASE_URL}{admin_path}"

                self.stderr.write(
                    f"{obj} failed validation.\n" f"\tERRORS: {errors}\n" f"\tLink to edit: {full_url}\n\n"
                )

        if error_count == 0:
            self.stdout.write(self.style.SUCCESS(f"\nAll {total_count} objects passed validation!"))
        else:
            self.stdout.write(
                self.style.WARNING(f"\nValidation complete. {error_count} objects failed out of {total_count}.")
            )

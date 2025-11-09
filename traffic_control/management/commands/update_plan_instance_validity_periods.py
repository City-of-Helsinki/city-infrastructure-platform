from django.core.management.base import BaseCommand

from traffic_control.mixins.models import ValidityPeriodModel
from traffic_control.models import Plan


class Command(BaseCommand):
    help = "Update validity_period_start of plan instances to their plan's decision_date"

    def handle(self, *args, **options):
        updated_count = 0

        def update_instances(plan, related_name):
            nonlocal updated_count
            for instance in getattr(plan, related_name).all():
                if isinstance(instance, ValidityPeriodModel) and instance.validity_period_start != plan.decision_date:
                    instance.validity_period_start = plan.decision_date
                    instance.save(update_fields=["validity_period_start"])
                    updated_count += 1

        related_names = [
            "barrier_plans",
            "mount_plans",
            "road_marking_plans",
            "signpost_plans",
            "traffic_light_plans",
            "traffic_sign_plans",
            "additional_sign_plans",
            "furniture_signpost_plans",
        ]

        for plan in Plan.objects.all():
            print("Updating plan instances with plan id:", plan.id)
            for related_name in related_names:
                update_instances(plan, related_name)

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} plan instances."))

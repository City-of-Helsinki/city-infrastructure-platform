import json
import os

from django.core.management.base import BaseCommand

from traffic_control.analyze_utils.plan_updater import PlanUpdater


class Command(BaseCommand):
    help = (
        "Updates plan information from given CSV file. CSV file has columns:"
        "Päätösnumero; Päätöspäivä; Nimi; Diaarinumero; Piirustusnumerot; Linkki."
        "Link to existing plans is decision_id (Päätösnumer)"
        "decision_date(Päätöspäivä), diary_number(Diaarinumero), drawing_numbers(Piirustusnumerot)"
        "and open_ahjo_link(Linkki) will be updated if plan with decision_number is found."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-pf",
            "--plan-file",
            type=str,
            required=True,
            help="CSV file with plan information. Expected encoding is utf-8-sig (BOM included in the file)",
        )
        parser.add_argument(
            "-d", "--dry-run", action="store_true", default=False, help="Dry run, only print what would be updated"
        )
        parser.add_argument(
            "-o",
            "--output-dir",
            type=str,
            required=False,
            default="plan_update_infos",
            help="Output directory for updated plan information",
        )

    def handle(self, *args, **options):
        plan_csv_file = options["plan_file"]
        dry_run = options["dry_run"]
        updater = PlanUpdater(plan_csv_file)
        if dry_run:
            self.stdout.write(self.style.NOTICE("Doing dry run, not updating data base"))

        self.stdout.write(self.style.NOTICE("Updating plans..."))
        updated, failed = updater.update_plans(do_db_update=not dry_run)
        self.stdout.write(self.style.SUCCESS(f"Updated {len(updated)} plans. "))
        self.stdout.write(self.style.ERROR(f"failed count: {len(failed)}"))
        self._write_result_jsons(updated, failed, options["output_dir"])
        self.stdout.write(self.style.SUCCESS(f"Done. Check results in {options['output_dir']}"))

    def _write_result_jsons(self, updated, failed, output_dir):
        with open(os.path.join(output_dir, "plan_fail_infos.json"), "w") as f:
            json.dump(failed, f, indent=4)
        with open(os.path.join(output_dir, "plan_update_infos.json"), "w") as f:
            json.dump(updated, f, indent=4)

import csv
import os

from django.core.management.base import BaseCommand

from traffic_control.analyze_utils.traffic_sign_data import TrafficSignAnalyzer, TrafficSignImporter


class Command(BaseCommand):
    help = "Analyzes sign input data"

    def add_arguments(self, parser):
        parser.add_argument(
            "-mf",
            "--mount-file",
            type=str,
            help="Path to the mount file in csv format",
        )
        parser.add_argument(
            "-sf",
            "--sign-file",
            type=str,
            help="Path to the sign file in csv format",
        )
        parser.add_argument(
            "-o",
            "--output-dir",
            type=str,
            default="streetdata_import_results",
            help="Path to the output directory where summary of results are dumped to",
        )
        parser.add_argument(
            "-u",
            "--update",
            action="store_true",
            dest="update",
            default=False,
            help="Try to update existing signs",
        )
        parser.add_argument(
            "-do",
            "--delete-orphan_mounts",
            action="store_true",
            dest="delete_orphan_mounts",
            default=False,
            help="Delete orphan mounts",
        )

    def handle(self, *args, **options):
        mount_file = options["mount_file"]
        if mount_file is None:
            self.stderr.write(self.style.ERROR("Missing mount file"))
            return None
        sign_file = options["sign_file"]
        if sign_file is None:
            self.stderr.write(self.style.ERROR("Missing sign file"))
            return None

        analyzer = TrafficSignAnalyzer(mount_file, sign_file)
        importer = TrafficSignImporter(
            analyzer.mounts_by_id, analyzer.signs_by_id, analyzer.additional_signs_by_id, options["update"]
        )
        results = importer.import_data()
        skipped_additional_signs = _get_skipped_additional_sign_results(results)
        skipped_signs = _get_skipped_sign_results(results)
        skipped_signposts = _get_skipped_signpost_results(results)
        _write_additional_sign_skip_results(list(skipped_additional_signs), options["output_dir"])
        _write_sign_skip_results(list(skipped_signs), options["output_dir"])
        _write_signpost_skip_results(list(skipped_signposts), options["output_dir"])
        _write_all_results(results, options["output_dir"])
        self.stdout.write(self.style.SUCCESS("Successfully imported sign data"))

        if options["delete_orphan_mounts"]:
            self.stdout.write(self.style.SUCCESS("Cleaning orphan mounts..."))
            importer.clean_orphan_mounts()
            self.stdout.write(self.style.SUCCESS("Orphan mounts cleaned"))


def _write_additional_sign_skip_results(results, output_dir):
    _write_results(results, output_dir, "additional_sign_skips.csv")


def _write_sign_skip_results(results, output_dir):
    _write_results(results, output_dir, "sign_skips.csv")


def _write_signpost_skip_results(results, output_dir):
    _write_results(results, output_dir, "signpost_skips.csv")


def _write_all_results(results, output_dir):
    _write_results(results, output_dir, "all_results.csv")


def _write_results(results, output_dir, filename):
    if len(results):
        headers = results[0].keys()
        with open(os.path.join(output_dir, filename), "w") as f:
            writer = csv.DictWriter(f, headers)
            writer.writerows(results)


def _is_additional_sign_skip(result):
    return _include_result(result, "skip", "additionalsign")


def _is_sign_skip(result):
    return _include_result(result, "skip", "sign")


def _is_signpost_skip(result):
    return _include_result(result, "skip", "signpost")


def _include_result(result, result_type, object_type):
    return result["result_type"] == result_type and result["object_type"] == object_type


def _get_skipped_additional_sign_results(results):
    return filter(_is_additional_sign_skip, results)


def _get_skipped_sign_results(results):
    return filter(_is_sign_skip, results)


def _get_skipped_signpost_results(results):
    return filter(_is_signpost_skip, results)

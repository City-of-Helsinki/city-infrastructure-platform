import json
import tablib

from django.core.management.base import BaseCommand

from traffic_control.analyze_utils.traffic_sign_data import TrafficSignAnalyzer


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

    def handle(self, *args, **options):
        import pprint
        pprint.pprint(args)
        pprint.pprint(options)
        mount_file = options["mount_file"]
        if mount_file is None:
            self.stderr.write(self.style.ERROR("Missing mount file"))
            return None
        sign_file = options["sign_file"]
        if sign_file is None:
            self.stderr.write(self.style.ERROR("Missing sign file"))
            return None

        analyzer = TrafficSignAnalyzer(mount_file, sign_file)
        reports = analyzer.analyze()
        for report in reports:
            if report['results']:
                self.stdout.write(f'writing report: {report["REPORT_TYPE"]}')
                with open(f'./anares/{report["REPORT_TYPE"]}.json', 'w') as outfile:
                    outfile.write(json.dumps(report['results'], indent=4))
                with open(f'./anares/{report["REPORT_TYPE"]}.xlsx', 'wb') as outfile:
                    data = tablib.Dataset(headers=report['results'][0].keys(), json=report['results'])
                    data.json = json.dumps(report['results'])
                    outfile.write(data.export('xlsx'))
            else:
                self.stdout.write(self.style.ERROR(f'empty report: {report["REPORT_TYPE"]}'))










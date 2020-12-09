from datetime import datetime
from urllib.request import urlretrieve

from django.contrib.gis.gdal import DataSource
from django.core.management import BaseCommand

from traffic_control.models import OperationalArea

SOURCE_NAME = "urakkarajat_katu"
WFS_SOURCE_URL = "https://kartta.hel.fi/ws/geoserver/avoindata/wfs"
SOURCE_LAYER = "Vastuualue_rya_urakkarajat"
DATE_FORMAT = "%Y-%m-%d"


def parse_date(date_str):
    return datetime.strptime(date_str, DATE_FORMAT).date()


class Command(BaseCommand):
    help = "Import operational areas from Helsinki WFS"

    def handle(self, *args, **options):
        self.stdout.write("Importing operational areas from Helsinki WFS ...")
        url = f"{WFS_SOURCE_URL}?service=wfs&version=2.0.0&request=GetFeature&typeNames={SOURCE_LAYER}"
        filename, _ = urlretrieve(url)
        ds = DataSource(filename)
        count = 0
        for feature in ds[0]:
            if feature["tehtavakokonaisuus"].value == "KATU":
                gdal_geometry = feature.geom
                gdal_geometry.coord_dim = 3  # force 3d coordinates
                start_date = parse_date(feature["alku_pvm"].value)
                end_date = parse_date(feature["loppu_pvm"].value)
                updated_date = parse_date(feature["paivitetty_tietopalveluun"].value)
                OperationalArea.objects.update_or_create(
                    source_name=SOURCE_NAME,
                    source_id=feature["id"].value,
                    defaults={
                        "name": feature["nimi"].value,
                        "name_short": feature["nimi_lyhyt"].value,
                        "area_type": feature["urakkamuoto"].value,
                        "contractor": feature["urakoitsija"].value,
                        "start_date": start_date,
                        "end_date": end_date,
                        "updated_date": updated_date,
                        "task": feature["tehtavakokonaisuus"].value,
                        "status": feature["status"].value,
                        "location": gdal_geometry.geos,
                    },
                )
                count += 1
        self.stdout.write(f"{count} features are imported.")

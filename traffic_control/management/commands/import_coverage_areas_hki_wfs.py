from datetime import datetime
from urllib.request import urlretrieve

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon
from django.core.management import BaseCommand

from traffic_control.models import Owner
from traffic_control.models.affect_area import CoverageArea, CoverageAreaCategory

SOURCE_NAME = "pysäköintialue"
WFS_SOURCE_URL = "https://kartta.hel.fi/ws/geoserver/avoindata/wfs"
SOURCE_LAYER = "Pysakointipaikat_alue"
DATE_FORMAT = "%Y-%m-%d"
OWNER_NAME = "City of Helsinki"


def parse_date(date_str):
    return datetime.strptime(date_str, DATE_FORMAT).date()


def parse_str_value(str_value):
    # string value can be None from WFS data, replace them with emtpy string
    return str_value or ""


class Command(BaseCommand):
    help = "Import coverage areas from Helsinki WFS"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.categories = {category.id: category for category in CoverageAreaCategory.objects.all()}

    def handle(self, *args, **options):
        self.stdout.write("Importing coverage areas from Helsinki WFS ...")
        url = f"{WFS_SOURCE_URL}?service=wfs&version=2.0.0&request=GetFeature&typeNames={SOURCE_LAYER}"
        filename, _ = urlretrieve(url)
        ds = DataSource(filename)
        count = 0
        owner = Owner.objects.get(name_en="City of Helsinki")
        for feature in ds[0]:
            category_id = feature["luokka"].value
            category_name = parse_str_value(feature["luokka_nimi"].value)
            category = self.get_coverage_area_category(category_id, category_name)
            gdal_geometry = feature.geom
            gdal_geometry.coord_dim = 3  # force 3d coordinates
            geometry = gdal_geometry.geos
            if geometry.geom_type == "Polygon":
                # the WFS layer has mixed geometries (Polygon & MultiPolygon)
                geometry = MultiPolygon([geometry])
            CoverageArea.objects.update_or_create(
                source_name=SOURCE_NAME,
                source_id=feature["id"].value,
                defaults={
                    "category": category,
                    "area_type": parse_str_value(feature["tyyppi"].value),
                    "season": parse_str_value(feature["kausi"].value),
                    "resident_parking_id": parse_str_value(feature["asukaspysakointitunnus"].value),
                    "place_position": parse_str_value(feature["paikan_asento"].value),
                    "validity": parse_str_value(feature["voimassaolo"].value),
                    "duration": parse_str_value(feature["kesto"].value),
                    "surface_area": feature["pinta_ala"].value,
                    "parking_slots": feature["paikat_ala"].value,
                    "additional_info": parse_str_value(feature["lisatieto"].value),
                    "stopping_prohibited": parse_str_value(feature["pysayttamiskielto"].value),
                    "updated_at": parse_date(feature["paivitetty_tietopalveluun"].value),
                    "owner": owner,
                    "location": geometry,
                },
            )
            count += 1
        self.stdout.write(f"{count} coverage areas are imported.")

    def get_coverage_area_category(self, category_id, category_name):
        if category_id not in self.categories:
            category = CoverageAreaCategory.objects.create(id=category_id, name=category_name)
            self.categories[category_id] = category
        return self.categories[category_id]

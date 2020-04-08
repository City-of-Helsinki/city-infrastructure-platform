import argparse
import csv
import os
from enum import Enum

import requests
from osgeo import ogr, osr
from requests.auth import HTTPBasicAuth


class LocationSpecifier(Enum):
    RIGHT = 1
    LEFT = 2


SOURCE_SRID = 4326
TARGET_SRID = 3879
SOURCE_NAME = "Vaisala 2019-2020"
OWNER = "Helsingin kaupunki"

parser = argparse.ArgumentParser(
    description="Send traffic sign reals to the platform from CSV-file"
)
parser.add_argument(
    "--username", required=True, type=str, help="Admin-username to make the import"
)
parser.add_argument(
    "--password", required=True, type=str, help="Admin-password to make the import"
)
parser.add_argument(
    "--url",
    required=True,
    type=str,
    default="http://localhost:8000/fi/api/traffic-sign-reals/",
    help="API-endpoint url where to post the data",
)
parser.add_argument(
    "--filename",
    required=True,
    default="../data/traffic_sign_reals_vaisala.csv",
    type=str,
    help="Path to the traffic sign codes csv file",
)

args = parser.parse_args()

filename = args.filename

if not os.path.exists(filename):
    raise Exception("File {0} does not exist".format(filename))

source = osr.SpatialReference()
source.ImportFromEPSG(SOURCE_SRID)

target = osr.SpatialReference()
target.ImportFromEPSG(TARGET_SRID)

transform = osr.CoordinateTransformation(source, target)

with open(filename, mode="r", encoding="utf-8-sig") as csv_file:
    auth = HTTPBasicAuth(args.username, args.password)
    csv_reader = csv.DictReader(csv_file, delimiter=",")
    counter = 0
    for row in csv_reader:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(
            float(row["longitude"].strip()), float(row["latitude"].strip()), 0.0
        )
        point.Transform(transform)
        point.SetCoordinateDimension(2)
        point.SetCoordinateDimension(3)
        try:
            location_specifier = LocationSpecifier[row["side"].strip().upper()].value
        except KeyError:
            location_specifier = None
        data = {
            "location": point.ExportToWkt(),
            "legacy_code": row["code"].strip(),
            "direction": row["heading"].strip(),
            "scanned_at": row["last_detected"].strip(),
            "location_specifier": location_specifier,
            "owner": OWNER,
            "operation": row["action"].strip(),
            "attachment_url": row["frame_url"].strip(),
            "is_active": True,
            "source_id": row["id"].strip(),
            "source_name": SOURCE_NAME,
        }
        print("Sending Traffic Sign Real: {0}".format(data))
        r = requests.post(url=args.url, data=data, auth=auth)
        print("{0} - {1} - {2}".format(r.status_code, r.reason, r.text))
        counter += 1

print("{0} traffic sign reals sent".format(counter))

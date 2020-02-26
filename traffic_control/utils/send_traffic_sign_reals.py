import argparse
import os

import requests
from osgeo import ogr
from requests.auth import HTTPBasicAuth

SOURCE_SRID = 3879
SOURCE_NAME = "BLOM streetview2019"
OWNER = "Helsingin kaupunki"
MOUNT_TYPES_EN_FI = {
    "Lightpole": "Katuvalopylväs",
    "Other": "Muu",
    "Pole": "Tolppa",
    "Portal": "Portaali",
    "Trafficlight": "Liikennevalopylväs",
    "Wall": "Seinä",
}

parser = argparse.ArgumentParser(
    description="""
        Send traffic sign real data to the platform from standard ESRI SHP-file.

        Note that SHP-metadata and related files (.shp, .shx, .dbf, .prj, .qix, .cpg)
        need to also exist the same folder.

        Shapefile is expected to have a single layer with PointZ geometries and following attributes:
            fid:String
            type:String
            text:String
            mount_type:String
            direction:String
            date:String
    """
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
    type=str,
    help="Path to the traffic sign reals shp file",
)

args = parser.parse_args()

filename = args.filename

if not os.path.exists(filename):
    raise Exception("File {0} does not exist".format(filename))

file = ogr.Open(filename)
layer = file.GetLayer(0)
print("SHP-file has {0} features.".format(layer.GetFeatureCount()))
auth = HTTPBasicAuth(args.username, args.password)
counter = 0
layer.ResetReading()

for feature in layer:
    print("Processing Feature ID: {0}".format(feature.GetFID()))
    feature_json = feature.ExportToJson(as_object=True)
    geometry = feature_json.get("geometry")
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint_2D(geometry.get("coordinates")[0], geometry.get("coordinates")[1])
    properties = feature_json.get("properties")
    data = {
        "location": "SRID={0};{1}".format(SOURCE_SRID, point.ExportToWkt()),
        "legacy_code": properties.get("type"),
        "txt": properties.get("text"),
        "mount_type": properties.get("mount_type"),
        "mount_type_fi": MOUNT_TYPES_EN_FI.get(properties.get("mount_type")),
        "direction": properties.get("direction"),
        "scanned_at": properties.get("date"),
        "owner": OWNER,
        "source_id": feature.GetFID(),
        "source_name": SOURCE_NAME,
    }
    print("Sending Traffic Sign Real: {0}".format(data))
    r = requests.post(url=args.url, data=data, auth=auth)
    print("{0} - {1} - {2}".format(r.status_code, r.reason, r.text))
    counter += 1

print("{0} traffic sign reals sent".format(counter))

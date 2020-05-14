import argparse
import csv
import os

import requests
from requests.auth import HTTPBasicAuth

parser = argparse.ArgumentParser(
    description="Send portal types to the platform from CSV-file"
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
    default="http://localhost:8000/v1/portal-types/",
    help="API-endpoint url where to post the data",
)
parser.add_argument(
    "--filename",
    required=True,
    default="../data/portal_types.csv",
    type=str,
    help="Path to the portal types csv file",
)

args = parser.parse_args()

filename = args.filename

if not os.path.exists(filename):
    raise Exception("File {0} does not exist".format(filename))

with open(filename, mode="r", encoding="utf-8-sig") as csv_file:
    auth = HTTPBasicAuth(args.username, args.password)
    csv_reader = csv.DictReader(csv_file, delimiter=",")
    counter = 0
    for row in csv_reader:
        structure = row["Rakenne"].strip()
        build_type = row["Tyyppi"].strip()
        model = row["Malli"].strip()
        data = {"structure": structure, "build_type": build_type, "model": model}
        print(
            "Sending Portal type: {0} - {1} - {2}".format(structure, build_type, model)
        )
        r = requests.post(url=args.url, data=data, auth=auth)
        print("{0} - {1} - {2}".format(r.status_code, r.reason, r.text))
        counter += 1

print("{0} portal types sent".format(counter))

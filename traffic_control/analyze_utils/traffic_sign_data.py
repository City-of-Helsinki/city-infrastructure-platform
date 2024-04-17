import csv

from django.contrib.gis.geos import Point


class TrafficSignAnalyzer:
    def __init__(self, mount_file, sign_file):
        self.mount_file = mount_file
        self.sign_file = sign_file

        self.mounts_by_id = self.get_objects_by_id(mount_file, "id", None, True)
        self.all_signs_by_id = self.get_objects_by_id(sign_file, "id", None, flat=True)
        self.signs_by_id = self.get_signs_by_id(sign_file, "id", flat=True)
        self.signs_by_mount_id = self.get_signs_by_mount_id()
        self.additional_signs_by_id = self.get_additional_signs_by_id(sign_file, "id", True)
        self.additional_signs_by_mount_id = self.get_additional_signs_by_mount_id()
        self.combine_mounts_with_signs(self.mounts_by_id,
                                       self.additional_signs_by_mount_id,
                                       self.signs_by_mount_id)
        self.no_mounts_per_sign_id = self.get_non_existing_mounts_by_sign_id()
        self.no_mounts_per_additional_sign_id = self.get_non_existing_mounts_by_additional_sign_id()

    def analyze(self):
        reports = [
            self.get_non_existing_mounts_for_additional_signs(),
            self.get_non_existing_mounts_for_signs(),
            self.get_mount_distances(),
            self.get_additional_sign_distances(),
            self.get_sign_distances(),
            self.get_mountless_additional_signs(),
            self.get_signless_additional_signs(),
            self.get_mountless_signs(),
        ]
        return reports

    @staticmethod
    def combine_mounts_with_signs(mounts_by_id, additional_signs_by_mount_id, signs_by_mount_id):
        # mounts should always just one entry
        for mount_id, data_d in mounts_by_id.items():
            data_d["additional_signs"] = []
            data_d["signs"] = []

            for entry in additional_signs_by_mount_id.get(mount_id, []):
                data_d["additional_signs"].append(entry)
            for entry in signs_by_mount_id.get(mount_id, []):
                data_d["signs"].append(entry)

    def get_mount_distances(self):
        distances = {}
        results = []
        for mount_id, data_d in self.mounts_by_id.items():
            distances[mount_id] = {}
            distances[mount_id]["additional_signs"] = self._get_distances_for_mount(data_d, "additional_signs")
            distances[mount_id]["signs"] = self._get_distances_for_mount(data_d, "signs")
            results.append({"mount_id": mount_id, "distance": distances[mount_id]})

        return {"REPORT_TYPE": "MOUNT DISTANCES", "results": results}

    @staticmethod
    def _get_distances_for_mount(mount_data, objects_field_name):
        distances = {}
        for entry in mount_data[objects_field_name]:
            distances.setdefault(entry["id"], []).append(entry["distance_to_mount"])
        return [{'mount_id': mount_data["id"], 'distances': distances}]

    def _get_mount_type(self, mount_id):
        return self.mounts_by_id.get(mount_id).get("tyyppi")

    @staticmethod
    def _get_code_for_sign(sign_id, signs_by_id):
        return signs_by_id.get(sign_id).get("merkkikoodi")

    def get_additional_sign_distances(self):
        results = map(
            lambda x: {"additional_sign_id": x.get("id"),
                       "sign_code": self._get_code_for_sign(x.get("id"), self.additional_signs_by_id),
                       "mount_id": x.get("kiinnityskohta_id"),
                       "mount_type": self._get_mount_type(x.get("kiinnityskohta_id")),
                       "distance_to_mount": x.get("distance_to_mount"), "parent_id": x.get("lisäkilven_päämerkin_id"),
                       "distance_to_parent": x.get("distance_to_parent"),
                       "parent_is_additional_sign": x.get("parent_is_additional_sign"),
                       "parent_code": x.get("parent_code"),},
            filter(lambda x: x.get("id") not in self.no_mounts_per_additional_sign_id,
                   self.additional_signs_by_id.values())
        )
        return {"REPORT_TYPE": "ADDITIONAL SIGN DISTANCES", "results": list(results)}

    def get_sign_distances(self):
        results = map(
            lambda x: {"sign_id": x.get("id"), "sign_code": self._get_code_for_sign(x.get("id"), self.signs_by_id),
                       "mount_id": x.get("kiinnityskohta_id"),
                       "mount_type": self._get_mount_type(x.get("kiinnityskohta_id")),
                       "distance_to_mount": x.get("distance_to_mount")},
            filter(lambda x: x.get("id") not in self.no_mounts_per_sign_id, self.signs_by_id.values()))
        return {"REPORT_TYPE": "SIGN DISTANCES", "results": list(results)}

    def get_mountless_additional_signs(self):
        return {"REPORT_TYPE": "MOUNTLESS ADDITIONAL SIGNS", "results": list(map(lambda x: {"id": x.get("id")},
                                                                                 filter(lambda x: not x[
                                                                                     "kiinnityskohta_id"].strip(),
                                                                                        self.additional_signs_by_id.values())))}

    def get_non_existing_mounts_for_additional_signs(self):
        return {"REPORT_TYPE": "NON EXISTING MOUNTS FOR ADDITIONAL SIGNS",
                "results": list(
                    map(lambda x: {"additional_sign_id": x[0], 'mount_id': x[1]},
                        self.no_mounts_per_additional_sign_id.items())
                )}

    def get_non_existing_mounts_for_signs(self):
        return {"REPORT_TYPE": "NON EXISTING MOUNTS FOR SIGNS",
                "results": list(
                    map(lambda x: {"sign_id": x[0], 'mount_id': x[1]}, self.no_mounts_per_sign_id.items())
                )}

    def get_non_existing_mounts_for_signs_old(self):
        return {"REPORT_TYPE": "NON EXISTING MOUNTS FOR SIGNS",
                "results": list(
                    map(
                        lambda x: {"sign_id": x.get("id"), "mount_id": x.get("kiinnityskohta_id"), },
                        filter(lambda x: x.get("kiinnityskohta_id").strip() not in self.mounts_by_id.keys(),
                               self.signs_by_id.values()
                               )
                    ))}

    def get_signless_additional_signs(self):
        return {"REPORT_TYPE": "SIGNLESSLESS ADDITIONAL SIGNS", "results": list(map(lambda x: {"id": x.get("id")},
                                                                                    filter(lambda x: not x[
                                                                                        "lisäkilven_päämerkin_id"].strip(),
                                                                                           self.additional_signs_by_id.values())))}

    def get_mountless_signs(self):
        return {"REPORT_TYPE": "MOUNTLESS SIGNS", "results": list(map(lambda x: {"id": x.get("id")},
                                                                      filter(
                                                                          lambda x: not x["kiinnityskohta_id"].strip(),
                                                                          self.signs_by_id.values())))}

    @staticmethod
    def get_objects_by_id(csv_file, id_field_name="id", filter_f=None, flat=False):
        objects_by_id = {}

        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if filter_f is None or filter_f(row):
                    if not flat:
                        objects_by_id.setdefault(row[id_field_name], []).append(row)
                    else:
                        objects_by_id[row[id_field_name]] = row

        return objects_by_id

    def get_additional_signs_by_id(self, csv_file, id_field_name="id", flat=False):
        additional_signs = self.get_objects_by_id(csv_file, id_field_name=id_field_name, filter_f=is_additional_sign,
                                                  flat=flat)
        for k, data in additional_signs.items():
            mount_data = self.mounts_by_id.get(data.get("kiinnityskohta_id"), None)
            if mount_data:
                mount_point = Point(float(mount_data["x"]), float(mount_data["y"]), 0.0)
                data["distance_to_mount"] = mount_point.distance(Point(float(data["x"]), float(data["y"]), 0.0))
            else:
                data["distance_to_mount"] = None
            parent_data = self.signs_by_id.get(data.get("lisäkilven_päämerkin_id"), None)
            if parent_data:
                parent_point = Point(float(parent_data["x"]), float(parent_data["y"]), 0.0)
                data["distance_to_parent"] = parent_point.distance(Point(float(data["x"]), float(data["y"]), 0.0))
                data["parent_is_additional_sign"] = "No"
                data["parent_code"] = parent_data.get('merkkikoodi')
            else:
                parent_data = self.all_signs_by_id.get(data.get("lisäkilven_päämerkin_id"), None)
                if parent_data:
                    parent_point = Point(float(parent_data["x"]), float(parent_data["y"]), 0.0)
                    data["distance_to_parent"] = parent_point.distance(Point(float(data["x"]), float(data["y"]), 0.0))
                    data["parent_is_additional_sign"] = "Yes"
                    data["parent_code"] = parent_data.get('merkkikoodi')
                else:
                    data["distance_to_parent"] = None
                    data["parent_is_additional_sign"] = None
                    data["parent_code"] = None
        return additional_signs

    def get_additional_signs_by_mount_id(self):
        additional_signs = {}
        for k, v in self.additional_signs_by_id.items():
            additional_signs.setdefault(v["kiinnityskohta_id"], []).append(v)
        return additional_signs

    def get_signs_by_id(self, csv_file, id_field_name="id", flat=False):
        signs = TrafficSignAnalyzer.get_objects_by_id(csv_file, id_field_name=id_field_name,
                                                      filter_f=lambda x: not is_additional_sign(x), flat=flat)
        for k, data in signs.items():
            mount_data = self.mounts_by_id.get(data.get("kiinnityskohta_id"), None)
            if mount_data:
                mount_point = Point(float(mount_data["x"]), float(mount_data["y"]), 0.0)
                data["distance_to_mount"] = mount_point.distance(Point(float(data["x"]), float(data["y"]), 0.0))
            else:
                data["distance_to_mount"] = None
        return signs

    def get_signs_by_mount_id(self):
        signs = {}
        for k, v in self.signs_by_id.items():
            signs.setdefault(v["kiinnityskohta_id"], []).append(v)
        return signs

    def get_non_existing_mounts_by_additional_sign_id(self):
        return {x.get("id"): x.get("kiinnityskohta_id") for x in
                filter(lambda x: x.get("kiinnityskohta_id").strip() not in self.mounts_by_id.keys(),
                       self.additional_signs_by_id.values()
                       )}

    def get_non_existing_mounts_by_sign_id(self):
        return {x.get("id"): x.get("kiinnityskohta_id") for x in
                filter(lambda x: x.get("kiinnityskohta_id").strip() not in self.mounts_by_id.keys(),
                       self.signs_by_id.values()
                       )}


def is_additional_sign(row):
    return row["merkkikoodi"][0] in ["H", "8"]

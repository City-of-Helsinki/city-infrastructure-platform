import csv
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Tuple, TypedDict, Union

from django.conf import settings
from django.contrib.gis.geos import Point

from traffic_control.enums import Condition, InstallationStatus
from traffic_control.models.additional_sign import AdditionalSignReal, Color
from traffic_control.models.common import Owner, TrafficControlDeviceType
from traffic_control.models.mount import LocationSpecifier as MountLocationSpecifier, MountReal, MountType
from traffic_control.models.signpost import SignpostReal
from traffic_control.models.traffic_sign import LocationSpecifier as SignLocationSpecifier, TrafficSignReal

TICKET_MACHINE_CODES = ["H20.91", "H20.92", "H20.93", "8591", "8592", "8593"]
VALUE_PATTERN = re.compile(r"^\d+(\.\d+)?")


class ImportResult(TypedDict):
    result_type: str
    object_type: str
    object_id: str
    reason: Union[str, None]


class CSVHeaders:
    id = "id"
    code = "merkkikoodi"
    color = "taustaväri"
    condition = "merkin_ehto"
    coord_x = "x"
    coord_y = "y"
    coord_z = "z"
    direction = "atsimuutti"
    height = "korkeus"
    location_specifier = "Sijaintitarkenne"
    mount_id = "kiinnityskohta_id"
    mount_type = "tyyppi"
    number_code = "numerokoodi"
    parent_sign_id = "lisäkilven_päämerkin_id"
    scanned_at = "tallennusajankohta"
    sign_mount_type = "kiinnitys"
    txt = "teksti"


class TrafficSignAnalyzer:
    def __init__(self, mount_file, sign_file):
        self.mount_file = mount_file
        self.sign_file = sign_file

        self.mounts_by_id = self.get_objects_by_id(mount_file, CSVHeaders.id, None, True)
        self.all_signs_by_id = self.get_objects_by_id(sign_file, CSVHeaders.id, None, flat=True)
        self.signs_by_id = self.get_signs_by_id(sign_file, CSVHeaders.id, flat=True)
        self.signs_by_mount_id = self.get_signs_by_mount_id()
        self.additional_signs_by_id = self.get_additional_signs_by_id(sign_file, CSVHeaders.id, True)
        self.additional_signs_by_mount_id = self.get_additional_signs_by_mount_id()
        self.combine_mounts_with_signs(self.mounts_by_id, self.additional_signs_by_mount_id, self.signs_by_mount_id)
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
            distances.setdefault(entry[CSVHeaders.id], []).append(entry["distance_to_mount"])
        return [{"mount_id": mount_data[CSVHeaders.id], "distances": distances}]

    def _get_mount_type(self, mount_id):
        return self.mounts_by_id.get(mount_id).get(CSVHeaders.mount_type)

    @staticmethod
    def _get_code_for_sign(sign_id, signs_by_id):
        return signs_by_id.get(sign_id).get(CSVHeaders.code)

    def get_additional_sign_distances(self):
        results = map(
            lambda x: {
                "additional_sign_id": x.get(CSVHeaders.id),
                "sign_code": self._get_code_for_sign(x.get(CSVHeaders.id), self.additional_signs_by_id),
                "mount_id": x.get(CSVHeaders.mount_id),
                "mount_type": self._get_mount_type(x.get(CSVHeaders.mount_id)),
                "distance_to_mount": x.get("distance_to_mount"),
                "parent_id": x.get(CSVHeaders.parent_sign_id),
                "distance_to_parent": x.get("distance_to_parent"),
                "parent_is_additional_sign": x.get("parent_is_additional_sign"),
                "parent_code": x.get("parent_code"),
            },
            filter(
                lambda x: x.get(CSVHeaders.id) not in self.no_mounts_per_additional_sign_id,
                self.additional_signs_by_id.values(),
            ),
        )
        return {"REPORT_TYPE": "ADDITIONAL SIGN DISTANCES", "results": list(results)}

    def get_sign_distances(self):
        results = map(
            lambda x: {
                "sign_id": x.get(CSVHeaders.id),
                "sign_code": self._get_code_for_sign(x.get("id"), self.signs_by_id),
                "mount_id": x.get(CSVHeaders.mount_id),
                "mount_type": self._get_mount_type(x.get(CSVHeaders.mount_id)),
                "distance_to_mount": x.get("distance_to_mount"),
            },
            filter(lambda x: x.get("id") not in self.no_mounts_per_sign_id, self.signs_by_id.values()),
        )
        return {"REPORT_TYPE": "SIGN DISTANCES", "results": list(results)}

    def get_mountless_additional_signs(self):
        return {
            "REPORT_TYPE": "MOUNTLESS ADDITIONAL SIGNS",
            "results": list(
                map(
                    lambda x: {CSVHeaders.id: x.get(CSVHeaders.id)},
                    filter(lambda x: not x[CSVHeaders.mount_id].strip(), self.additional_signs_by_id.values()),
                )
            ),
        }

    def get_non_existing_mounts_for_additional_signs(self):
        return {
            "REPORT_TYPE": "NON EXISTING MOUNTS FOR ADDITIONAL SIGNS",
            "results": list(
                map(
                    lambda x: {"additional_sign_id": x[0], "mount_id": x[1]},
                    self.no_mounts_per_additional_sign_id.items(),
                )
            ),
        }

    def get_non_existing_mounts_for_signs(self):
        return {
            "REPORT_TYPE": "NON EXISTING MOUNTS FOR SIGNS",
            "results": list(map(lambda x: {"sign_id": x[0], "mount_id": x[1]}, self.no_mounts_per_sign_id.items())),
        }

    def get_signless_additional_signs(self):
        return {
            "REPORT_TYPE": "SIGNLESSLESS ADDITIONAL SIGNS",
            "results": list(
                map(
                    lambda x: {CSVHeaders.id: x.get(CSVHeaders.id)},
                    filter(lambda x: not x[CSVHeaders.parent_sign_id].strip(), self.additional_signs_by_id.values()),
                ),
            ),
        }

    def get_mountless_signs(self):
        return {
            "REPORT_TYPE": "MOUNTLESS SIGNS",
            "results": list(
                map(
                    lambda x: {CSVHeaders.id: x.get(CSVHeaders.id)},
                    filter(lambda x: not x[CSVHeaders.mount_id].strip(), self.signs_by_id.values()),
                )
            ),
        }

    @staticmethod
    def get_objects_by_id(csv_file, id_field_name=CSVHeaders.id, filter_f=None, flat=False):
        objects_by_id = {}

        with open(csv_file) as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                if filter_f is None or filter_f(row):
                    if not flat:
                        objects_by_id.setdefault(row[id_field_name], []).append(row)
                    else:
                        objects_by_id[row[id_field_name]] = row

        return objects_by_id

    def get_additional_signs_by_id(self, csv_file, id_field_name=CSVHeaders.id, flat=False):
        additional_signs = self.get_objects_by_id(
            csv_file, id_field_name=id_field_name, filter_f=is_additional_sign, flat=flat
        )
        for k, data in additional_signs.items():
            mount_data = self.mounts_by_id.get(data.get(CSVHeaders.mount_id), None)
            if mount_data:
                mount_point = Point(float(mount_data[CSVHeaders.coord_x]), float(mount_data[CSVHeaders.coord_y]), 0.0)
                data["distance_to_mount"] = mount_point.distance(
                    Point(float(data[CSVHeaders.coord_x]), float(data[CSVHeaders.coord_y]), 0.0)
                )
            else:
                data["distance_to_mount"] = None
            parent_data = self.signs_by_id.get(data.get(CSVHeaders.parent_sign_id), None)
            if parent_data:
                parent_point = Point(
                    float(parent_data[CSVHeaders.coord_x]), float(parent_data[CSVHeaders.coord_y]), 0.0
                )
                data["distance_to_parent"] = parent_point.distance(
                    Point(float(data[CSVHeaders.coord_x]), float(data[CSVHeaders.coord_y]), 0.0)
                )
                data["parent_is_additional_sign"] = "No"
                data["parent_code"] = parent_data.get(CSVHeaders.code)
            else:
                parent_data = self.all_signs_by_id.get(data.get(CSVHeaders.parent_sign_id), None)
                if parent_data:
                    parent_point = Point(
                        float(parent_data[CSVHeaders.coord_x]), float(parent_data[CSVHeaders.coord_y]), 0.0
                    )
                    data["distance_to_parent"] = parent_point.distance(
                        Point(float(data[CSVHeaders.coord_x]), float(data[CSVHeaders.coord_y]), 0.0)
                    )
                    data["parent_is_additional_sign"] = "Yes"
                    data["parent_code"] = parent_data.get(CSVHeaders.code)
                else:
                    data["distance_to_parent"] = None
                    data["parent_is_additional_sign"] = None
                    data["parent_code"] = None
        return additional_signs

    def get_additional_signs_by_mount_id(self):
        additional_signs = {}
        for k, v in self.additional_signs_by_id.items():
            additional_signs.setdefault(v[CSVHeaders.mount_id], []).append(v)
        return additional_signs

    def get_signs_by_id(self, csv_file, id_field_name=CSVHeaders.id, flat=False):
        signs = TrafficSignAnalyzer.get_objects_by_id(
            csv_file, id_field_name=id_field_name, filter_f=lambda x: not is_additional_sign(x), flat=flat
        )
        for k, data in signs.items():
            mount_data = self.mounts_by_id.get(data.get(CSVHeaders.mount_id), None)
            if mount_data:
                mount_point = Point(float(mount_data[CSVHeaders.coord_x]), float(mount_data[CSVHeaders.coord_y]), 0.0)
                data["distance_to_mount"] = mount_point.distance(
                    Point(float(data[CSVHeaders.coord_x]), float(data[CSVHeaders.coord_y]), 0.0)
                )
            else:
                data["distance_to_mount"] = None
        return signs

    def get_signs_by_mount_id(self):
        signs = {}
        for k, v in self.signs_by_id.items():
            signs.setdefault(v[CSVHeaders.mount_id], []).append(v)
        return signs

    def get_non_existing_mounts_by_additional_sign_id(self):
        return {
            x.get(CSVHeaders.id): x.get(CSVHeaders.mount_id)
            for x in filter(
                lambda x: x.get(CSVHeaders.mount_id).strip() not in self.mounts_by_id.keys(),
                self.additional_signs_by_id.values(),
            )
        }

    def get_non_existing_mounts_by_sign_id(self):
        return {
            x.get(CSVHeaders.id): x.get(CSVHeaders.mount_id)
            for x in filter(
                lambda x: x.get(CSVHeaders.mount_id).strip() not in self.mounts_by_id.keys(),
                self.signs_by_id.values(),
            )
        }


class TrafficSignImporter:
    SOURCE_NAME = "StreetScan"

    def __init__(self, mount_data, sign_data, additional_sign_data, update=False):
        self.update = update
        self.mount_data = mount_data
        self.sign_data = sign_data
        self.additional_sign_data = additional_sign_data
        self.mount_types_by_name = self._get_mount_types_by_name()
        self.default_owner = self._get_default_owner()
        self.device_types_by_code = self._get_device_types_by_code()

        self.mount_reals_by_source_id = None
        self.sign_reals_by_source_id = None

        self.results = [ImportResult]

    def import_data(self):
        self._import_mount_reals()
        self._import_sign_data()
        self._import_signpost_data()
        self._import_additional_sign_data()

        return self.results

    def _import_mount_reals(self):
        skip_source_ids = set()
        update_by_source_ids = {}
        # Django missing feature: https://code.djangoproject.com/ticket/34943
        # so cannot do update on conflict
        if self.update:
            existing_mount_reals_by_source_id = self._get_mount_real_objects_by_source_id()
            for source_id, mount_real in existing_mount_reals_by_source_id.items():
                skip, update_data = self.compare_csv_mount_to_db_values(source_id, mount_real)
                if skip:
                    skip_source_ids.add(source_id)
                elif update_data:
                    update_by_source_ids[source_id] = update_data

            for source_id, update_data in update_by_source_ids.items():
                (
                    MountReal.objects.filter(source_id=source_id, source_name=TrafficSignImporter.SOURCE_NAME).update(
                        **update_data
                    )
                )

        MountReal.objects.bulk_create(
            self._get_mount_objects(skip_source_ids, update_by_source_ids.keys()),
            batch_size=1000,
            ignore_conflicts=True,
        )
        self.mount_reals_by_source_id = self._get_mount_reals_by_source_id()
        return skip_source_ids, update_by_source_ids

    def compare_csv_mount_to_db_values(self, source_id, mount_real) -> Tuple[bool, dict[str, Any]]:
        csv_data = self.mount_data.get(source_id, None)
        if csv_data is None:
            # entry in db but not in csv -> do nothing
            return True, {}

        return False, self._compare_common_csv_values_to_db_values(mount_real, csv_data)

    def _get_mount_objects(self, skip_source_ids, update_source_ids):
        for mount_source_id, mount_data in self.mount_data.items():
            if mount_source_id not in skip_source_ids and mount_source_id not in update_source_ids:
                location_specifier = mount_data[CSVHeaders.location_specifier]
                yield MountReal(
                    mount_type=self.mount_types_by_name[mount_data[CSVHeaders.mount_type]],
                    source_id=mount_source_id,
                    source_name=self.SOURCE_NAME,
                    location=Point(
                        float(mount_data[CSVHeaders.coord_x]),
                        float(mount_data[CSVHeaders.coord_y]),
                        float(mount_data[CSVHeaders.coord_z]),
                        srid=settings.SRID,
                    ),
                    owner=self.default_owner,
                    installation_status=get_default_installation_status(),
                    location_specifier=MountLocationSpecifier(int(location_specifier)) if location_specifier else None,
                    scanned_at=self._get_sign_scanned_at(mount_data.get(CSVHeaders.scanned_at)),
                )

    def _import_sign_data(self):
        skip_source_ids = set()
        update_by_source_ids = {}
        if self.update:
            existing_sign_reals_by_source_id = self._get_sign_real_objects_by_source_id()
            for source_id, sign_real in existing_sign_reals_by_source_id.items():
                skip, update_data = self.compare_csv_sign_to_db_values(source_id, sign_real)
                if skip:
                    skip_source_ids.add(source_id)
                elif update_data:
                    update_by_source_ids[source_id] = update_data

            for source_id, update_data in update_by_source_ids.items():
                (
                    TrafficSignReal.objects.filter(
                        source_id=source_id, source_name=TrafficSignImporter.SOURCE_NAME
                    ).update(**update_data)
                )

        TrafficSignReal.objects.bulk_create(
            self._get_sign_objects(skip_source_ids, update_by_source_ids.keys()), batch_size=1000, ignore_conflicts=True
        )
        self.sign_reals_by_source_id = self._get_sign_reals_by_source_id()
        return skip_source_ids, update_by_source_ids

    def compare_csv_sign_to_db_values(self, source_id, sign_real):
        csv_data = self.sign_data.get(source_id, None)
        if csv_data is None:
            # entry in db but not in csv -> do nothing
            return True, {}

        update_data = self._compare_common_csv_values_to_db_values(sign_real, csv_data)
        update_data.update(self._compare_common_sign_csv_values_to_db_values(sign_real, csv_data))

        update_data.update(
            self._get_update_for_value(sign_real, "value", self._get_sign_value(csv_data[CSVHeaders.number_code]))
        )

        update_data.update(self._get_update_for_value(sign_real, "txt", csv_data[CSVHeaders.txt]))

        return False, update_data

    def _get_sign_objects(self, skip_source_ids, update_source_ids):
        for sign_source_id, sign_data in self.sign_data.items():
            if (
                not is_signpost(sign_data)
                and sign_source_id not in skip_source_ids
                and sign_source_id not in update_source_ids
            ):
                if not should_be_ignored_totally(sign_data):
                    yield TrafficSignReal(
                        owner=self.default_owner,
                        device_type=self._get_sign_device_type(sign_data[CSVHeaders.code]),
                        scanned_at=self._get_sign_scanned_at(sign_data.get(CSVHeaders.scanned_at)),
                        value=self._get_sign_value(sign_data.get(CSVHeaders.number_code)),
                        source_id=sign_source_id,
                        source_name=self.SOURCE_NAME,
                        location=Point(
                            float(sign_data[CSVHeaders.coord_x]),
                            float(sign_data[CSVHeaders.coord_y]),
                            float(sign_data[CSVHeaders.coord_z]),
                            srid=settings.SRID,
                        ),
                        direction=get_sign_direction(sign_data),
                        height=self._get_sign_height(sign_data.get(CSVHeaders.height)),
                        condition=get_sign_condition(sign_data),
                        mount_real_id=self._get_mount_real_id(sign_data[CSVHeaders.mount_id], sign_source_id, "sign"),
                        mount_type=self.mount_types_by_name[sign_data[CSVHeaders.sign_mount_type]],
                        txt=sign_data[CSVHeaders.txt],
                        installation_status=get_default_installation_status(),
                        location_specifier=get_sign_location_specifier(sign_data),
                    )
                else:
                    self.results.append(
                        ImportResult(
                            result_type="skip",
                            object_type="sign",
                            object_id=sign_source_id,
                            reason=sign_data[CSVHeaders.code],
                        )
                    )

    def _import_signpost_data(self):
        skip_source_ids = set()
        update_source_ids = {}
        if self.update:
            # signpost import and update are totally skipped for now
            # So implementation will be done later if needed for the update
            pass
        SignpostReal.objects.bulk_create(
            self._get_signpost_objects(skip_source_ids, update_source_ids.keys()),
            batch_size=1000,
            ignore_conflicts=True,
        )

    def _get_signpost_objects(self, skip_source_ids, update_source_ids):
        for sign_source_id, sign_data in self.sign_data.items():
            if (
                is_signpost(sign_data)
                and sign_source_id not in skip_source_ids
                and sign_source_id not in update_source_ids
            ):
                if not should_be_ignored_totally(sign_data) and sign_post_should_be_imported(sign_data):
                    yield SignpostReal(
                        owner=self.default_owner,
                        device_type=self._get_sign_device_type(sign_data[CSVHeaders.code]),
                        value=self._get_sign_value(sign_data.get(CSVHeaders.number_code)),
                        source_id=sign_source_id,
                        source_name=self.SOURCE_NAME,
                        location=Point(
                            float(sign_data[CSVHeaders.coord_x]),
                            float(sign_data[CSVHeaders.coord_y]),
                            float(sign_data[CSVHeaders.coord_z]),
                            srid=settings.SRID,
                        ),
                        direction=get_sign_direction(sign_data),
                        height=self._get_sign_height(sign_data.get(CSVHeaders.height)),
                        condition=get_sign_condition(sign_data),
                        mount_real_id=self._get_mount_real_id(
                            sign_data[CSVHeaders.mount_id], sign_source_id, "signpost"
                        ),
                        mount_type=self.mount_types_by_name[CSVHeaders.sign_mount_type],
                        txt=sign_data[CSVHeaders.txt],
                        installation_status=get_default_installation_status(),
                        location_specifier=get_sign_location_specifier(sign_data),
                        scanned_at=self._get_sign_scanned_at(sign_data.get(CSVHeaders.scanned_at)),
                    )
                else:
                    self.results.append(
                        ImportResult(
                            result_type="skip",
                            object_type="signpost",
                            object_id=sign_source_id,
                            reason=sign_data[CSVHeaders.code],
                        )
                    )

    def _import_additional_sign_data(self):
        skip_source_ids = set()
        update_by_source_ids = {}
        if self.update:
            existing_additional_sign_reals_by_source_id = self._get_additional_sign_real_objects_by_source_id()
            for source_id, asign_real in existing_additional_sign_reals_by_source_id.items():
                skip, update_data = self._compare_csv_additional_sign_to_db_values(source_id, asign_real)
                if skip:
                    skip_source_ids.add(source_id)
                elif update_data:
                    update_by_source_ids[source_id] = update_data

            for source_id, update_data in update_by_source_ids.items():
                (
                    AdditionalSignReal.objects.filter(
                        source_id=source_id, source_name=TrafficSignImporter.SOURCE_NAME
                    ).update(**update_data)
                )

        AdditionalSignReal.objects.bulk_create(
            self._get_additional_sign_objects(skip_source_ids, update_by_source_ids.keys()),
            batch_size=1000,
            ignore_conflicts=True,
        )
        return skip_source_ids, update_by_source_ids

    def _compare_csv_additional_sign_to_db_values(self, source_id, sign_real):
        csv_data = self.additional_sign_data.get(source_id, None)
        if csv_data is None:
            # entry in db but not in csv -> do nothing
            return True, {}

        update_data = self._compare_common_csv_values_to_db_values(sign_real, csv_data)
        update_data.update(self._compare_common_sign_csv_values_to_db_values(sign_real, csv_data))

        update_data.update(
            self._get_update_for_value(
                sign_real,
                "parent_id",
                self._get_sign_real_id(csv_data[CSVHeaders.parent_sign_id], source_id, "additionalsign"),
            )
        )

        update_data.update(self._get_update_for_value(sign_real, "color", get_additional_sign_color(csv_data)))

        update_data.update(
            self._get_update_for_value(
                sign_real,
                "additional_information",
                get_additional_information(csv_data),
            )
        )

        update_data.update(self._get_update_for_value(sign_real, "missing_content", True))

        return False, update_data

    def _get_additional_sign_objects(self, skip_source_ids, update_source_ids):
        for sign_source_id, sign_data in self.additional_sign_data.items():
            if (
                additional_sign_should_be_imported(sign_data)
                and is_additional_sign(sign_data)
                and sign_source_id not in skip_source_ids
                and sign_source_id not in update_source_ids
            ):
                yield AdditionalSignReal(
                    owner=self.default_owner,
                    device_type=self._get_sign_device_type(sign_data[CSVHeaders.code]),
                    scanned_at=self._get_sign_scanned_at(sign_data.get(CSVHeaders.scanned_at)),
                    source_id=sign_source_id,
                    source_name=self.SOURCE_NAME,
                    location=Point(
                        float(sign_data[CSVHeaders.coord_x]),
                        float(sign_data[CSVHeaders.coord_y]),
                        float(sign_data[CSVHeaders.coord_z]),
                        srid=settings.SRID,
                    ),
                    direction=get_sign_direction(sign_data),
                    height=self._get_sign_height(sign_data.get(CSVHeaders.height)),
                    condition=get_sign_condition(sign_data),
                    mount_real_id=self._get_mount_real_id(
                        sign_data[CSVHeaders.mount_id], sign_source_id, "additionalsign"
                    ),
                    mount_type=self.mount_types_by_name[sign_data[CSVHeaders.sign_mount_type]],
                    parent_id=self._get_sign_real_id(
                        sign_data[CSVHeaders.parent_sign_id], sign_source_id, "additionalsign"
                    ),
                    installation_status=get_default_installation_status(),
                    location_specifier=get_sign_location_specifier(sign_data),
                    color=get_additional_sign_color(sign_data),
                    additional_information=get_additional_information(sign_data),
                    missing_content=True,
                )
            else:
                self.results.append(
                    ImportResult(
                        result_type="skip",
                        object_type="additionalsign",
                        object_id=sign_source_id,
                        reason=sign_data[CSVHeaders.code],
                    )
                )

    def _get_mount_real_id(self, source_id, related_id, object_type):
        db_id = self.mount_reals_by_source_id.get(source_id, None)

        if db_id is None:
            (
                self.results.append(
                    ImportResult(
                        result_type="error",
                        object_type="mount_real",
                        object_id=source_id,
                        reason=f"Mount Not Found for {object_type}: {related_id}",
                    ),
                ),
            )

        return db_id

    def _get_sign_real_id(self, source_id, related_id, object_type):
        db_id = self.sign_reals_by_source_id.get(source_id, None)

        if db_id is None:
            (
                self.results.append(
                    ImportResult(
                        result_type="error",
                        object_type="sign",
                        object_id=source_id,
                        reason=f"Sign Not Found for {object_type}: {related_id}",
                    ),
                ),
            )

        return db_id

    def _get_mount_reals_by_source_id(self):
        return {x.source_id: x.id for x in MountReal.objects.filter(source_name=self.SOURCE_NAME)}

    def _get_mount_real_objects_by_source_id(self):
        return {x.source_id: x for x in MountReal.objects.filter(source_name=self.SOURCE_NAME)}

    def _get_sign_reals_by_source_id(self):
        return {x.source_id: x.id for x in TrafficSignReal.objects.filter(source_name=self.SOURCE_NAME)}

    def _get_sign_real_objects_by_source_id(self):
        return {x.source_id: x for x in TrafficSignReal.objects.filter(source_name=self.SOURCE_NAME)}

    def _get_additional_sign_real_objects_by_source_id(self):
        return {x.source_id: x for x in AdditionalSignReal.objects.filter(source_name=self.SOURCE_NAME)}

    @staticmethod
    def _get_sign_scanned_at(date_str):
        """Need to add 00 to the end as source date has only +00 as tz marker"""
        return datetime.strptime(date_str + "00", "%Y/%m/%d %H:%M:%S%z")

    @staticmethod
    def _get_sign_value(value):
        """Sign value is consist from 1 or 2 string separated by whitespace
        Actual used value is in the 1st string
        """
        m = VALUE_PATTERN.match(value.strip().replace(",", "."))
        if m:
            return Decimal(m.group())
        else:
            return None

    def _get_sign_device_type(self, code):
        dcode = self.device_types_by_code.get(code, None)
        if not dcode:
            self.results.append(
                ImportResult(
                    result_type="error", object_type="device_type", object_id=code, reason="dtype code not found"
                )
            )
        return dcode

    @staticmethod
    def _get_sign_height(height):
        """Height in csv is in meters, internally we use centimeters"""
        return int(float(height) * 100)

    @staticmethod
    def _get_mount_types_by_name():
        mount_types = list(MountType.objects.all())
        by_fi = {mt.description_fi: mt for mt in mount_types}
        by_en = {mt.description: mt for mt in mount_types}
        by_fi.update(by_en)
        return by_fi

    @staticmethod
    def _get_default_owner():
        return Owner.objects.get(name_fi="Helsingin kaupunki")

    @staticmethod
    def _get_device_types_by_code():
        return {dt.code: dt for dt in list(TrafficControlDeviceType.objects.all())}

    @staticmethod
    def _get_update_for_value(db_obj, db_field_name, csv_value):
        if getattr(db_obj, db_field_name) != csv_value:
            return {db_field_name: csv_value}
        return {}

    def _compare_common_csv_values_to_db_values(self, object_real, csv_data):
        update_data = {}

        mount_type_field_name = (
            CSVHeaders.mount_type if isinstance(object_real, MountReal) else CSVHeaders.sign_mount_type
        )
        update_data.update(
            self._get_update_for_value(
                object_real, "mount_type", self.mount_types_by_name.get(csv_data.get(mount_type_field_name))
            )
        )

        update_data.update(
            self._get_update_for_value(
                object_real, "scanned_at", self._get_sign_scanned_at(csv_data.get(CSVHeaders.scanned_at))
            )
        )

        csv_location_specifier_value = csv_data[CSVHeaders.location_specifier]
        location_speficier_class = (
            MountLocationSpecifier if isinstance(object_real, MountReal) else SignLocationSpecifier
        )
        csv_location_specifier = (
            location_speficier_class(int(csv_location_specifier_value)) if csv_location_specifier_value else None
        )
        update_data.update(self._get_update_for_value(object_real, "location_specifier", csv_location_specifier))

        csv_point = Point(
            float(csv_data[CSVHeaders.coord_x]),
            float(csv_data[CSVHeaders.coord_y]),
            float(csv_data[CSVHeaders.coord_z]),
            srid=settings.SRID,
        )
        update_data.update(self._get_update_for_value(object_real, "location", csv_point))

        return update_data

    def _compare_common_sign_csv_values_to_db_values(self, object_real, csv_data):
        update_data = {}
        update_data.update(
            self._get_update_for_value(
                object_real, "device_type", self._get_sign_device_type(csv_data[CSVHeaders.code])
            )
        )

        update_data.update(self._get_update_for_value(object_real, "direction", get_sign_direction(csv_data)))

        update_data.update(
            self._get_update_for_value(object_real, "height", self._get_sign_height(csv_data[CSVHeaders.height]))
        )

        update_data.update(self._get_update_for_value(object_real, "condition", get_sign_condition(csv_data)))

        update_data.update(
            self._get_update_for_value(
                object_real,
                "mount_real_id",
                self._get_mount_real_id(csv_data[CSVHeaders.mount_id], object_real.source_id, "sign"),
            )
        )

        return update_data


def is_additional_sign(row):
    code = row[CSVHeaders.code]
    return code[0] in ["H", "8"] and code not in TICKET_MACHINE_CODES


def is_signpost(row):
    code = row[CSVHeaders.code]
    return (
        code[0] in ["6", "7", "F", "G"]
        and code[0:2] not in ["65", "62"]
        and not code.startswith("F24")
        and not code.startswith("F8.1")
    )


def sign_post_should_be_imported(row):
    """Signpost imports should not be done yet"""
    return False


def should_be_ignored_totally(row):
    return row[CSVHeaders.code] in ["x", "not classified"]


def additional_sign_should_be_imported(row):
    if row[CSVHeaders.txt] == "unreadable":
        return False
    if not row[CSVHeaders.parent_sign_id].strip():
        # these are "lippuautomaatit"
        return row[CSVHeaders.code] in TICKET_MACHINE_CODES
    return True


def get_default_installation_status():
    return InstallationStatus.IN_USE


def get_sign_location_specifier(sign_data):
    code = sign_data[CSVHeaders.code]
    location_specifier_value = sign_data[CSVHeaders.location_specifier]
    if location_specifier_value:
        return SignLocationSpecifier(int(location_specifier_value))

    if code in ["4171", "4172", "418", "D3.1", "D3.1_2", "D3.2", "D3.2_2", "D3.3", "D3.3_2"]:
        return SignLocationSpecifier(4)

    return None


def get_sign_direction(sign_data):
    return int(sign_data.get(CSVHeaders.direction))


def get_sign_condition(sign_data):
    return Condition(int(sign_data.get(CSVHeaders.condition)))


def get_additional_information(sign_data):
    """Combine teksti and numerokoodi fields from cvs for additional_information.
    format is "text: <text_from_csv>; numbercode: <code_from_csv"
    """
    return f"text:{sign_data[CSVHeaders.txt].strip()}; numbercode:{sign_data[CSVHeaders.number_code].strip()}"


def get_additional_sign_color(sign_data):
    try:
        color = int(sign_data[CSVHeaders.color])
    except ValueError:
        return None

    if color:
        try:
            return Color(color)
        except ValueError:
            return None

    return None

import csv
import re
from datetime import datetime
from typing import Dict, List, NamedTuple

from traffic_control.models.plan import Plan

DRAWING_NUMBER_PATTERN = re.compile(r"\d+-\d+")


class PlanUpdateData(NamedTuple):
    decision_date: datetime
    diary_number: str
    drawing_numbers: List[str]
    decision_url: str


class CSVHeader:
    decision_id = "Päätösnumero"
    decision_date = "Päätöspäivä"
    name = "Nimi"
    diary_number = "Diaarinumero"
    drawing_numbers = "Piirustusnumerot"
    decision_url = "Linkki"


class PlanUpdater:
    def __init__(self, plan_csv_file_path):
        self.plan_csv_file_path = plan_csv_file_path
        self.plan_update_data_by_decision_id = self._get_plan_update_data()

    def _get_plan_update_data(self) -> Dict[str, PlanUpdateData]:
        update_data_by_decision_id = {}

        with open(self.plan_csv_file_path, mode="r", encoding="utf-8-sig") as plan_csv_file:
            reader = csv.DictReader(plan_csv_file, delimiter=";")
            for row in reader:
                update_data_by_decision_id[row[CSVHeader.decision_id]] = PlanUpdateData(
                    diary_number=row[CSVHeader.diary_number],
                    drawing_numbers=[dn.strip() for dn in row[CSVHeader.drawing_numbers].split(",")],
                    decision_date=self._get_decision_datetime(row[CSVHeader.decision_date]),
                    decision_url=row[CSVHeader.decision_url],
                )

        return update_data_by_decision_id

    @staticmethod
    def _get_decision_datetime(date_str: str) -> datetime:
        """date format in the csv is dd-md-yyyy, eg 13.1.2012"""
        return datetime.strptime(date_str, "%d.%m.%Y")

    def update_plans(self, do_db_update=False):
        failed_decision_by_decision_id = {}
        successfully_updated = {}
        for decision_id, update_data in self.plan_update_data_by_decision_id.items():
            actual_update_data = self._get_update_params(update_data)
            if do_db_update:
                try:
                    # just to get exceptions incase not found or too many found
                    Plan.objects.get(decision_id=decision_id)
                    Plan.objects.filter(decision_id=decision_id).update(**actual_update_data)
                    successfully_updated[decision_id] = self._get_json_serializable_update_data(actual_update_data)
                except Exception as e:
                    failed_decision_by_decision_id[decision_id] = {
                        "update_data": self._get_json_serializable_update_data(actual_update_data),
                        "exception": str(e),
                    }
            else:
                try:
                    Plan.objects.get(decision_id=decision_id)
                    successfully_updated[decision_id] = self._get_json_serializable_update_data(actual_update_data)
                except Exception as e:
                    failed_decision_by_decision_id[decision_id] = {
                        "update_data": self._get_json_serializable_update_data(actual_update_data),
                        "exception": str(e),
                    }

        return successfully_updated, failed_decision_by_decision_id

    @staticmethod
    def _get_update_params(update_data):
        return {
            "diary_number": update_data.diary_number or None,
            "drawing_numbers": PlanUpdater._get_legal_drawing_numbers(update_data.drawing_numbers),
            "decision_url": update_data.decision_url,
            "decision_date": update_data.decision_date,
        }

    @staticmethod
    def _get_legal_drawing_numbers(drawing_numbers: List[str]) -> List[str]:
        return list(filter(lambda x: DRAWING_NUMBER_PATTERN.match(x), drawing_numbers))

    @staticmethod
    def _get_json_serializable_update_data(actual_update_data):
        actual_update_data["decision_date"] = actual_update_data["decision_date"].isoformat()
        return actual_update_data

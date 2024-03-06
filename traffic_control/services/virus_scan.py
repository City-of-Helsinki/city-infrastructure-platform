from typing import List, TypedDict

import requests
from django.conf import settings


class VirusScanError(TypedDict):
    detail: str
    viruses: List[str]


class VirusScanResponse(TypedDict):
    status_code: int
    errors: List[VirusScanError]


def clam_av_scan(files, api_version="v1") -> VirusScanResponse:
    response = requests.post(get_clam_av_scan_url(api_version), files=files)
    return _handle_clam_av_response(response)


def get_clam_av_scan_url(api_version: str) -> str:
    return f"{settings.CLAMAV_BASE_URL}/api/{api_version}/scan"


def _handle_clam_av_response(response) -> VirusScanResponse:
    status_code = response.status_code
    if status_code != 200:
        return VirusScanResponse(
            status_code=status_code,
            errors=[VirusScanError(detail="Status code not 200", viruses=["ClamAV response not OK"])],
        )

    errors = _get_errors_from_response_json(response.json())
    return VirusScanResponse(status_code=status_code, errors=errors)


def _get_errors_from_response_json(json_response) -> List[VirusScanError]:
    errors = []
    for result_d in json_response["data"]["result"]:
        if result_d["is_infected"]:
            errors.append(VirusScanError(detail=f"{result_d['name']} is infected", viruses=result_d["viruses"]))

    return errors

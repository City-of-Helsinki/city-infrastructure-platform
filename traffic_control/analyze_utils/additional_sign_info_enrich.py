import csv
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, NamedTuple, Tuple, Union

from django.db import transaction

from traffic_control.models import AdditionalSignReal, ParkingZoneUpdateInfo, TrafficControlDeviceType


class AdditionalSignInfoUpdateInfo(NamedTuple):
    additional_sign_id: str
    location: str
    device_type_code: str
    old_additional_information: str
    new_additional_information: str
    streetsmart_link: str
    admin_link: str
    content_schema: Union[Dict[str, Any], None]
    errors: List[str]


def _get_admin_link(additional_sign_id: str) -> str:
    """TDOO now just hardcoded production admin link"""
    return f"https://cityinfra.api.hel.fi/en/admin/traffic_control/additionalsignreal/{additional_sign_id}/change/"


def _get_content_schema_update(
    additional_sign: AdditionalSignReal, content_s: Union[Dict[str, str], None]
) -> Union[Dict, None]:
    """Do not get content schema update if additional sign has it already"""
    if not additional_sign.content_s and additional_sign.missing_content is True:
        dt = TrafficControlDeviceType.objects.get(code=additional_sign.device_type.code)
        if dt.content_schema and content_s:
            return content_s
    return None


def _get_error_info(additional_sign: AdditionalSignReal, errors: List[str]) -> AdditionalSignInfoUpdateInfo:
    return AdditionalSignInfoUpdateInfo(
        additional_sign_id=str(additional_sign.id),
        location=additional_sign.location.ewkt,
        device_type_code=additional_sign.device_type.code,
        old_additional_information=additional_sign.additional_information,
        new_additional_information="",
        streetsmart_link=additional_sign.attachment_url,
        admin_link=_get_admin_link(str(additional_sign.id)),
        content_schema=None,
        errors=errors,
    )


def _get_success_info(
    additional_sign: AdditionalSignReal, new_additional_information, content_s: Union[Dict[str, str], None] = None
) -> AdditionalSignInfoUpdateInfo:
    return AdditionalSignInfoUpdateInfo(
        additional_sign_id=str(additional_sign.id),
        location=additional_sign.location.ewkt,
        device_type_code=additional_sign.device_type.code,
        old_additional_information=additional_sign.additional_information,
        new_additional_information=new_additional_information,
        streetsmart_link=additional_sign.attachment_url,
        admin_link=_get_admin_link(str(additional_sign.id)),
        content_schema=_get_content_schema_update(additional_sign, content_s),
        errors=[],
    )


SUPPORTED_DTYPE_CODES = [
    "H20.71",
    "H20.71S",
    "H20.72",
    "H20.72S",
    "H20.73",
    "H20.73S",
    "H20.74",
    "H20.74S",
    "H20.75",
    "H20.75S",
    "H20.8",
    "H20.8S",
]


TEXT_NUMBERCODE_PATTERN = re.compile(r"text:\s*(.*?);\s*numbercode:\s*(.*)")
PERMIT_REPLACEMENT_PATTERN = re.compile(r"(\b\w+\b)\s*/(\b\w+\b)")
ZONE_LIMIT_VALUE_PATTERN = re.compile(r"(\d+)\s+(\d+)\s+(min|h)|(\d+)\s*(\d+)(min|h|mın)")
ALLOWED_PERMIT_VALUES = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Z",
    "A/B",
    "A/F",
    "B/C",
    "C/E",
    "F/H",
    "H/L",
    "I/J",
    "J/K",
]


ALLOWED_ZONE_VALUES = ["1", "2", "3"]
ALLOWED_UNIT_VALUES = ["min", "h"]
H20_71X_BASIC_ERROR_STR = "Could not get zone and permit from additional_information"
H20_72X_BASIC_ERROR_STR = "Could not get zone, limit and unit from additional_information"
TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR = "text and numbercode not found from additional_information"
H20_71_FORMAT_STR = "Vyöhyke/Zon {zone}. Ei koske P-tunnuksella/Gäller ej med P-tecknet {permit}"
H20_71S_FORMAT_STR = "Vyöhyke/Zon {zone}. Maksu ei koske P-tunnuksella/Avgiften gäller ej med P-tecknet {permit}"
H20_8_FORMAT_STR = "Ei koske P-tunnuksella/Gäller ej med P-tecknet {permit}"
H20_8S_FORMAT_STR = "Maksu ei koske P-tunnuksella/Avgiften gäller ej med P-tecknet {permit}"


def h20_73_handler(additional_sign: AdditionalSignReal):
    return basic_str_handler(additional_sign, "Vyöhyke/Zon 1")


def h20_74_handler(additional_sign: AdditionalSignReal):
    return basic_str_handler(additional_sign, "Vyöhyke/Zon 2")


def h20_75_handler(additional_sign: AdditionalSignReal):
    return basic_str_handler(additional_sign, "Vyöhyke/Zon 3")


def h20_8_handler(additional_sign: AdditionalSignReal):
    return _get_h20_8x_update_info(additional_sign, H20_8_FORMAT_STR)


def h20_8s_handler(additional_sign: AdditionalSignReal) -> AdditionalSignInfoUpdateInfo:
    return _get_h20_8x_update_info(additional_sign, H20_8S_FORMAT_STR)


def h20_71_handler(additional_sign: AdditionalSignReal) -> AdditionalSignInfoUpdateInfo:
    return _get_h20_71x_update_info(additional_sign, H20_71_FORMAT_STR)


def h20_71s_handler(additional_sign: AdditionalSignReal) -> AdditionalSignInfoUpdateInfo:
    return _get_h20_71x_update_info(additional_sign, H20_71S_FORMAT_STR)


def h20_72_handler(additional_sign: AdditionalSignReal) -> AdditionalSignInfoUpdateInfo:
    return get_h20_72x_update_info(
        additional_sign, "Vyöhyke/Zon {zone}. Kertamaksu enintään/Engångsbetalning max {limit} {unit}"
    )


def h20_72s_handler(additional_sign: AdditionalSignReal) -> AdditionalSignInfoUpdateInfo:
    return get_h20_72x_update_info(
        additional_sign, "Vyöhyke/Zon {zone}. Kertamaksu enintään/Engångsbetalning max {limit} {unit}"
    )


def get_h20_72x_update_info(additional_sign: AdditionalSignReal, text_format_str: str) -> AdditionalSignInfoUpdateInfo:
    text_value, numbercode_value = _get_text_and_numbercode_values(additional_sign.additional_information)
    if text_value is None or numbercode_value is None:
        return _get_error_info(additional_sign, [TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR])

    zone, limit, unit = _get_zone_limit_and_unit_from_h20_72_text(text_value)
    if zone is None and limit is None and unit is None:
        return _get_error_info(additional_sign, [H20_72X_BASIC_ERROR_STR])

    errors = []
    if zone not in ALLOWED_ZONE_VALUES:
        errors.append(f"Parsed zone is not allowed: {zone}")
    if unit not in ALLOWED_UNIT_VALUES:
        errors.append(f"Parsed unit is not allowed: {unit}")
    if errors:
        return _get_error_info(additional_sign, errors)

    return _get_success_info(
        additional_sign,
        _make_additional_information_str(text_format_str.format(zone=zone, limit=limit, unit=unit), numbercode_value),
        {"zone": zone, "limit": limit, "unit": unit},
    )


def _get_h20_71x_update_info(additional_sign: AdditionalSignReal, text_format_str: str) -> AdditionalSignInfoUpdateInfo:
    text_value, numbercode_value = _get_text_and_numbercode_values(additional_sign.additional_information)
    if text_value is None and numbercode_value is None:
        return _get_error_info(additional_sign, [TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR])

    zone, permit_code = _get_zone_and_permit_from_h20_71x_text(text_value)
    if zone is None and permit_code is None:
        return _get_error_info(additional_sign, [H20_71X_BASIC_ERROR_STR])

    errors = []
    if permit_code not in ALLOWED_PERMIT_VALUES:
        errors.append(f"Parsed permit code is not allowed: {permit_code}")
    if zone not in ALLOWED_ZONE_VALUES:
        errors.append(f"Parsed zone is not allowed: {zone}")
    if errors:
        return _get_error_info(additional_sign, errors)

    return _get_success_info(
        additional_sign,
        _make_additional_information_str(
            _h20_71x_additional_sign_text(zone, permit_code, text_format_str), numbercode_value
        ),
        {"zone": zone, "permit": permit_code},
    )


def _get_h20_8x_update_info(additional_sign: AdditionalSignReal, text_format_str: str) -> AdditionalSignInfoUpdateInfo:
    text_value, numbercode_value = _get_text_and_numbercode_values(additional_sign.additional_information)

    if text_value is None or numbercode_value is None:
        return _get_error_info(additional_sign, [TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR])

    permit_code = _get_permit_from_h20_8_text(text_value)
    if not permit_code:
        return _get_error_info(additional_sign, ["Could not get permit code from additional_information"])
    else:
        if permit_code not in ALLOWED_PERMIT_VALUES:
            return _get_error_info(additional_sign, [f"Parsed permit code is not allowed: {permit_code}"])
        else:
            return _get_success_info(
                additional_sign,
                _make_additional_information_str(
                    _h20_8_additional_sign_text(permit_code, text_format_str), numbercode_value
                ),
                {"permit": permit_code},
            )


def _h20_8_additional_sign_text(permit_code: str, text_format_str: str) -> str:
    return text_format_str.format(permit=permit_code)


def _h20_71x_additional_sign_text(zone: str, permit_code: str, text_format_str: str) -> str:
    return text_format_str.format(zone=zone, permit=permit_code)


def _get_permit_from_h20_8_text(text: str) -> Union[str, None]:
    stripped_text = text.replace("unreadable", "").strip()
    # after this there should be only one substring left that should be the permit code
    # if not then it should be reported as an error
    if len(stripped_text.split()) != 1:
        return None

    return _map_permit_code(stripped_text.upper())


def _get_zone_and_permit_from_h20_71x_text(text: str) -> Tuple[str | None, str | None]:
    """Known formats are '<zone>;<permit_code> and '<zone> <permit_code>'
    Any other is considered to be erroneous data.
    """
    parts = re.sub(PERMIT_REPLACEMENT_PATTERN, r"\1/\2", text).replace(";", " ").split()
    if len(parts) != 2:
        return None, None

    return parts[0].strip(), _map_permit_code(parts[1].strip().upper())


def _get_zone_limit_and_unit_from_h20_72_text(text: str) -> Tuple[str | None, str | None, str | None]:
    pre_cleaned = text.replace(";", " ")
    match = re.match(ZONE_LIMIT_VALUE_PATTERN, pre_cleaned)
    if match:
        if match.group(1):
            # format with spaces eg. 1 20 min
            zone = match.group(1)
            limit = match.group(2)
            unit = match.group(3)
        else:
            # format without spaces eg. 1 20min
            zone = match.group(4)
            limit = match.group(5)
            unit = match.group(6)

        return zone, limit, _map_unit(unit)

    return None, None, None


def _map_permit_code(permit_code: str) -> str:
    """Currently just map 0 to O. Streetscan data has interpreted many O to 0"""
    if permit_code == "0":
        return "O"
    return permit_code


def _map_unit(unit: str) -> str:
    """in streetscan data what is supposed to be min is actually mın (with dotless I)"""
    if unit == "mın":
        return "min"
    return unit


def basic_str_handler(additional_sign: AdditionalSignReal, hardcoded_text: str) -> AdditionalSignInfoUpdateInfo:
    text_value, number_value = _get_text_and_numbercode_values(additional_sign.additional_information)
    if text_value is not None and number_value is not None:
        return _get_success_info(additional_sign, _make_additional_information_str(hardcoded_text, number_value))

    return _get_error_info(additional_sign, [TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR])


def _get_default_queryset():
    """Exclude is so that those simple Vyökyke additional signs are not handled twice"""
    return (
        AdditionalSignReal.objects.filter(device_type__code__in=SUPPORTED_DTYPE_CODES)
        .exclude(additional_information__icontains="vyöhyke")
        .exclude(additional_information__icontains="Ei koske P-tunnuksella")
        .select_related("device_type")
    )


def _get_text_and_numbercode_values(additional_info_str: str) -> Tuple[Any, Any]:
    match = re.search(TEXT_NUMBERCODE_PATTERN, _pre_clean_additional_info(additional_info_str))
    if match:
        return match.group(1), match.group(2)
    return None, None


def _pre_clean_additional_info(additional_info_str: str) -> str:
    # handle case where permit code is 'A  /B'
    pre_cleaned_text = additional_info_str.replace("\n", "")
    return pre_cleaned_text


def _make_additional_information_str(text_value: str, numbercode_value: str) -> str:
    return f"text:{text_value}; numbercode:{numbercode_value}"


HANDLERS_BY_DTYPE_CODE = {
    "H20.71": h20_71_handler,
    "H20.71S": h20_71s_handler,
    "H20.72": h20_72_handler,
    "H20.72S": h20_72s_handler,
    "H20.73": h20_73_handler,
    "H20.73S": h20_73_handler,
    "H20.74": h20_74_handler,
    "H20.74S": h20_74_handler,
    "H20.75": h20_75_handler,
    "H20.75S": h20_75_handler,
    "H20.8": h20_8_handler,
    "H20.8S": h20_8s_handler,
}


def get_update_infos(qset=None):
    if qset is None:
        qset = _get_default_queryset()

    update_infos = []
    for additional_sign in qset:
        dtype_code = additional_sign.device_type.code
        if not HANDLERS_BY_DTYPE_CODE.get(dtype_code):
            update_infos.append(_get_error_info(additional_sign, [[f"Device type: {dtype_code} not supported"]]))
        else:
            update_infos.append(HANDLERS_BY_DTYPE_CODE[dtype_code](additional_sign))

    return update_infos


def get_error_infos(
    update_infos: List[AdditionalSignInfoUpdateInfo], order_by="device_type_code"
) -> List[AdditionalSignInfoUpdateInfo]:
    return sorted((filter(lambda x: x.errors, update_infos)), key=lambda x: getattr(x, order_by))


def get_success_infos(
    update_infos: List[AdditionalSignInfoUpdateInfo], order_by="device_type_code"
) -> List[AdditionalSignInfoUpdateInfo]:
    return sorted((filter(lambda x: not x.errors, update_infos)), key=lambda x: getattr(x, order_by))


def do_database_update(
    update_infos: List[AdditionalSignInfoUpdateInfo], update_errors: List[AdditionalSignInfoUpdateInfo]
) -> Union[ParkingZoneUpdateInfo, None]:
    def get_update_params():
        ud_params = {"additional_information": update_info.new_additional_information}
        if update_info.content_schema:
            ud_params["content_s"] = update_info.content_schema
            ud_params["missing_content"] = False
        return ud_params

    with transaction.atomic():
        start_time = datetime.now(timezone.utc)
        for update_info in update_infos:
            AdditionalSignReal.objects.filter(id=update_info.additional_sign_id).update(**get_update_params())
        end_time = datetime.now(timezone.utc)
        return ParkingZoneUpdateInfo.objects.create(
            start_time=start_time,
            end_time=end_time,
            update_infos=update_infos,
            database_update=True,
            update_errors=update_errors,
        )


def write_infos_to_csv(update_infos: List[AdditionalSignInfoUpdateInfo], file_path):
    headers = [
        "additional_sign_id",
        "location",
        "device_type_code",
        "old_additional_information",
        "new_additional_information",
        "streetsmart_link",
        "admin_link",
        "errors",
    ]
    with open(file_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        writer.writerow(headers)
        writer.writerows(update_infos)


def _rows_for_csv(update_infos: List[AdditionalSignInfoUpdateInfo]):
    for update_info in update_infos:
        yield [
            update_info.additional_sign_id,
            update_info.location,
            update_info.device_type_code,
            update_info.old_additional_information,
            update_info.new_additional_information,
            update_info.streetsmart_link,
            update_info.admin_link,
            ";".join(update_info.errors),
        ]

import re
from typing import Any, List, NamedTuple, Optional, Tuple, TypedDict, Union

from traffic_control.models import AdditionalSignReal

class AdditionalSignInfoUpdateInfo(NamedTuple):
    additional_sign_id: str
    device_type_code: str
    old_additional_information: str
    new_additional_information: str
    errors: List[str]


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


#TEXT_NUMBERCODE_PATTERN = re.compile( r"text:\s*([^;]*);\s*numbercode:\s*([^;]*)")
TEXT_NUMBERCODE_PATTERN = re.compile(r"text:\s*(.+?);\s*numbercode:\s*(.*)")
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
    "J/K"
]

def h20_73_handler(additional_sign: AdditionalSignReal):
    return basic_str_handler(additional_sign, "Vyöhyke/Zon 1")


def h20_74_handler(additional_sign: AdditionalSignReal):
    return basic_str_handler(additional_sign, "Vyöhyke/Zon 2")


def h20_75_handler(additional_sign: AdditionalSignReal):
    return basic_str_handler(additional_sign, "Vyöhyke/Zon 3")


def h20_8_handler(additional_sign: AdditionalSignReal):
    return _get_h20_8x_update_info(
        additional_sign, "Ei koske P-tunnuksella/Gäller ej med P-tecknet {permit}"
    )

def h20_8s_handler(additional_sign: AdditionalSignReal) -> AdditionalSignInfoUpdateInfo:
    return _get_h20_8x_update_info(
        additional_sign, "Maksu ei koske P-tunnuksella/Avgiften gäller ej med P-tecknet {permit}"
    )

def _get_h20_8x_update_info(additional_sign: AdditionalSignReal, text_format_str: str) -> AdditionalSignInfoUpdateInfo:
    print("JF handling ads", additional_sign.id)
    text_value, numbercode_value = _get_text_and_numbercode_values(additional_sign.additional_information)
    print("JF: text_value", text_value)
    print("JF: numbercode_value", numbercode_value)

    if text_value is None and numbercode_value is  None:
        return AdditionalSignInfoUpdateInfo(
            additional_sign_id=str(additional_sign.id),
            device_type_code=additional_sign.device_type.code,
            old_additional_information=additional_sign.additional_information,
            new_additional_information="",
            errors=["text and numbercode not found from additional_information"]
        )
    permit_code = _get_permit_from_h20_8_text(text_value)
    if not permit_code:
        return AdditionalSignInfoUpdateInfo(
            additional_sign_id=str(additional_sign.id),
            device_type_code=additional_sign.device_type.code,
            old_additional_information=additional_sign.additional_information,
            new_additional_information="",
            errors=["Could not get permit code from additional_information"],
        )
    else:
        if permit_code not in ALLOWED_PERMIT_VALUES:
            return AdditionalSignInfoUpdateInfo(
                additional_sign_id=str(additional_sign.id),
                device_type_code=additional_sign.device_type.code,
                old_additional_information=additional_sign.additional_information,
                new_additional_information="",
                errors=[f"Parsed permit code is not allowed: {permit_code}"],
            )
        else:

            return AdditionalSignInfoUpdateInfo(
                additional_sign_id=str(additional_sign.id),
                device_type_code=additional_sign.device_type.code,
                old_additional_information=additional_sign.additional_information,
                new_additional_information=_make_additional_information_str(
                    _h20_8_additional_sign_text(permit_code, text_format_str), numbercode_value
                ),
                errors=[]
            )


def _h20_8_additional_sign_text(permit_code: str, text_format_str:str) -> str:
    return text_format_str.format(permit = permit_code)


def _get_permit_from_h20_8_text(text: str) -> Union[str, None]:
    stripped_text = text.replace("unreadable", "").strip()
    # after this there should be only one substring left that should be the permit code
    # if not then it should be reported as an error
    if len(stripped_text.split()) != 1:
        return None

    return _map_permit_code(stripped_text)

def _map_permit_code(permit_code: str) -> str:
    """Currently just map 0 to O. Streetscan data has interpreted many O to 0"""
    if permit_code == '0':
        return 'O'
    return permit_code


def basic_str_handler(additional_sign: AdditionalSignReal, hardcoded_text: str, format_params=None) -> AdditionalSignInfoUpdateInfo:
    text_value, number_value = _get_text_and_numbercode_values(additional_sign.additional_information)
    print(f"JF {text_value}: {number_value}")
    if text_value is not None and number_value is not None:
        return AdditionalSignInfoUpdateInfo(
            additional_sign_id=str(additional_sign.id),
            device_type_code=additional_sign.device_type.code,
            old_additional_information=additional_sign.additional_information,
            new_additional_information=_make_additional_information_str(hardcoded_text, number_value),
            errors=[],
        )

    return AdditionalSignInfoUpdateInfo(
        additional_sign_id=str(additional_sign.id),
        device_type_code=additional_sign.device_type.code,
        old_additional_information=additional_sign.additional_information,
        new_additional_information="",
        errors=["text and numbercode not found from additional_information"]
    )


def _get_default_queryset():
    return AdditionalSignReal.objects.filter(device_type__code__in=SUPPORTED_DTYPE_CODES).select_related("device_type")

def _get_text_and_numbercode_values(additional_info_str: str) -> Tuple[Any, Any]:
    print("JF get text and number code from", additional_info_str)
    match = re.search(TEXT_NUMBERCODE_PATTERN, additional_info_str)
    if match:
        return match.group(1), match.group(2)
    return None, None

def _make_additional_information_str(text_value: str, numbercode_value: str) -> str:
    return f"text:{text_value}; numbercode:{numbercode_value}"


HANDLERS_BY_DTYPE_CODE = {
    "H20.71": None,
    "H20.71S": None,
    "H20.72": None,
    "H20.72S": None,
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
            update_infos.append(AdditionalSignInfoUpdateInfo(
                additional_sign_id=additional_sign.id,
                device_type_code=dtype_code,
                old_additional_information=additional_sign.additional_information,
                new_additional_information="",
                errors=[f"Device type: {dtype_code} not suppoerted"],
                )
            )
        else:
            update_infos.append(HANDLERS_BY_DTYPE_CODE[dtype_code](additional_sign))

    return update_infos

def get_error_infos(update_infos: List[AdditionalSignInfoUpdateInfo]) -> List[AdditionalSignInfoUpdateInfo]:
    return list(filter(lambda x: x.errors, update_infos))

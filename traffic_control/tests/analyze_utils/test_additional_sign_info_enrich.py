import pytest

from traffic_control.analyze_utils.additional_sign_info_enrich import (
    do_database_update,
    get_update_infos,
    H20_8_FORMAT_STR,
    H20_8S_FORMAT_STR,
    H20_71_FORMAT_STR,
    H20_71S_FORMAT_STR,
    H20_71X_BASIC_ERROR_STR,
    H20_72X_BASIC_ERROR_STR,
    TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR,
)
from traffic_control.tests.factories import AdditionalSignRealFactory, TrafficControlDeviceTypeFactory


def _get_h20_71x_params(dtype_code):
    def get_text_part(zone, permit):
        if dtype_code == "H20.71":
            return H20_71_FORMAT_STR.format(zone=zone, permit=permit)
        elif dtype_code == "H20.71S":
            return H20_71S_FORMAT_STR.format(zone=zone, permit=permit)

    return (
        (
            dtype_code,
            "text:;numbercode:",
            "",
            [H20_71X_BASIC_ERROR_STR],
        ),
        (
            dtype_code,
            "text:2;numbercode:",
            "",
            [H20_71X_BASIC_ERROR_STR],
        ),
        (
            dtype_code,
            "",
            "",
            [TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR],
        ),
        (
            dtype_code,
            "text:6 A; numbercode:",
            "",
            ["Parsed zone is not allowed: 6"],
        ),
        (
            dtype_code,
            "text:3 ASD; numbercode:",
            "",
            ["Parsed permit code is not allowed: ASD"],
        ),
        (
            dtype_code,
            "text:6 ASD; numbercode:",
            "",
            ["Parsed permit code is not allowed: ASD", "Parsed zone is not allowed: 6"],
        ),
        (
            dtype_code,
            "text:3 A/B; numbercode:asda",
            f"text:{get_text_part(3, 'A/B')}; numbercode:asda",
            [],
        ),
        (
            dtype_code,
            "text:3; a/b; numbercode:asda",
            f"text:{get_text_part(3, 'A/B')}; numbercode:asda",
            [],
        ),
        (
            dtype_code,
            "text:3 A\n/B; numbercode:asda",
            f"text:{get_text_part(3, 'A/B')}; numbercode:asda",
            [],
        ),
        (
            dtype_code,
            "text:3 ; A/\nB; numbercode:asda",
            f"text:{get_text_part(3, 'A/B')}; numbercode:asda",
            [],
        ),
    )


def _get_h20_72x_params(dtype_code):
    return (
        (dtype_code, "text:;numbercode:", "", [H20_72X_BASIC_ERROR_STR]),
        (dtype_code, "text:2;numbercode:", "", [H20_72X_BASIC_ERROR_STR]),
        (dtype_code, "text:2 60;numbercode:", "", [H20_72X_BASIC_ERROR_STR]),
        (
            dtype_code,
            "",
            "",
            [TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR],
        ),
        (
            dtype_code,
            "text:6 60 min; numbercode:",
            "",
            ["Parsed zone is not allowed: 6"],
        ),
        (
            dtype_code,
            "text:2 60 sekunttei; numbercode:",
            "",
            [H20_72X_BASIC_ERROR_STR],
        ),
        (
            dtype_code,
            "text:2 60 min; numbercode:",
            "text:Vyöhyke/Zon 2. Kertamaksu enintään/Engångsbetalning max 60 min; numbercode:",
            [],
        ),
        (
            dtype_code,
            "text:2 60min; numbercode:",
            "text:Vyöhyke/Zon 2. Kertamaksu enintään/Engångsbetalning max 60 min; numbercode:",
            [],
        ),
        (
            dtype_code,
            "text:3;50min; numbercode:",
            "text:Vyöhyke/Zon 3. Kertamaksu enintään/Engångsbetalning max 50 min; numbercode:",
            [],
        ),
    )


def _get_h20_73x_params(dtype_code):
    return (
        (
            dtype_code,
            "",
            "",
            [TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR],
        ),
        (
            dtype_code,
            "text:;numbercode:",
            "text:Vyöhyke/Zon 1; numbercode:",
            [],
        ),
        (
            dtype_code,
            "text:anything;numbercode:anything",
            "text:Vyöhyke/Zon 1; numbercode:anything",
            [],
        ),
    )


def _get_h20_74x_params(dtype_code):
    return (
        (
            dtype_code,
            "",
            "",
            [TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR],
        ),
        (
            dtype_code,
            "text:;numbercode:",
            "text:Vyöhyke/Zon 2; numbercode:",
            [],
        ),
        (
            dtype_code,
            "text:anything;numbercode:anything",
            "text:Vyöhyke/Zon 2; numbercode:anything",
            [],
        ),
    )


def _get_h20_75x_params(dtype_code):
    return (
        (
            dtype_code,
            "",
            "",
            [TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR],
        ),
        (
            dtype_code,
            "text:;numbercode:",
            "text:Vyöhyke/Zon 3; numbercode:",
            [],
        ),
        (
            dtype_code,
            "text:anything;numbercode:anything",
            "text:Vyöhyke/Zon 3; numbercode:anything",
            [],
        ),
    )


def _get_h20_8x_params(dtype_code):
    def get_text_part(permit):
        if dtype_code == "H20.8":
            return H20_8_FORMAT_STR.format(permit=permit)
        elif dtype_code == "H20.8S":
            return H20_8S_FORMAT_STR.format(permit=permit)

    return (
        (
            dtype_code,
            "",
            "",
            [TEXT_NUMBERCODE_NOT_FOUND_ERROR_STR],
        ),
        (dtype_code, "text:;numbercode:", "", ["Could not get permit code from additional_information"]),
        (dtype_code, "text: NOTALLOWED; numbercode:", "", ["Parsed permit code is not allowed: NOTALLOWED"]),
        (dtype_code, "text: A/B; numbercode:", f"text:{get_text_part('A/B')}; numbercode:", []),
        (dtype_code, "text: a/B; numbercode:", f"text:{get_text_part('A/B')}; numbercode:", []),
        (dtype_code, "text: \na/\nb; numbercode:", f"text:{get_text_part('A/B')}; numbercode:", []),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "dtype_code, additional_information, expected_new_info, expected_errors",
    _get_h20_71x_params("H20.71")
    + _get_h20_71x_params("H20.71S")
    + _get_h20_72x_params("H20.72")
    + _get_h20_72x_params("H20.72S")
    + _get_h20_73x_params("H20.73")
    + _get_h20_73x_params("H20.73S")
    + _get_h20_74x_params("H20.74")
    + _get_h20_74x_params("H20.74S")
    + _get_h20_75x_params("H20.75")
    + _get_h20_75x_params("H20.75S")
    + _get_h20_8x_params("H20.8")
    + _get_h20_8x_params("H20.8S"),
)
def test_additional_sign_info_enrich(dtype_code, additional_information, expected_new_info, expected_errors):
    adsr = AdditionalSignRealFactory(device_type__code=dtype_code, additional_information=additional_information)
    update_info = get_update_infos()
    assert len(update_info) == 1

    assert update_info[0].additional_sign_id == str(adsr.id)
    assert update_info[0].device_type_code == dtype_code
    assert update_info[0].old_additional_information == additional_information
    assert update_info[0].new_additional_information == expected_new_info
    assert update_info[0].streetsmart_link == adsr.attachment_url
    assert update_info[0].errors == expected_errors


@pytest.mark.django_db
def test_additional_sign_info_do_database_update():
    dt = TrafficControlDeviceTypeFactory(code="H20.8", content_schema={"jotain": "jossain"})
    adsr1 = AdditionalSignRealFactory(
        device_type=dt, additional_information="text: A/B; numbercode:", content_s=None, missing_content=True
    )
    adsr2 = AdditionalSignRealFactory(
        device_type=dt, additional_information="text: A/B; numbercode:", content_s={"test": "me"}, missing_content=False
    )
    update_infos = get_update_infos()
    pz_update_info_o = do_database_update(update_infos, [])
    adsr1.refresh_from_db()
    assert adsr1.missing_content is False
    assert adsr1.content_s == {"permit": "A/B"}
    assert adsr1.additional_information == "text:Ei koske P-tunnuksella/Gäller ej med P-tecknet A/B; numbercode:"

    adsr2.refresh_from_db()
    assert adsr2.missing_content is False
    assert adsr2.content_s == {"test": "me"}
    assert adsr2.additional_information == "text:Ei koske P-tunnuksella/Gäller ej med P-tecknet A/B; numbercode:"

    assert pz_update_info_o.database_update is True
    assert pz_update_info_o.update_infos == update_infos

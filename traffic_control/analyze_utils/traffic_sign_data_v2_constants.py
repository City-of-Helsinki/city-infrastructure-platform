"""Constants and CSV header definitions for TrafficSignAnalyzerV2."""
import re

# Constants for V2 analyzer
VALID_STATUS_VALUES = ["new", "unchanged", "changed", "removed"]  # Lowercase for case-insensitive comparison
ZEBRA_CROSSING_LEFT_CODES = ["511", "5112", "E1_2"]
ZEBRA_CROSSING_RIGHT_CODES = ["5111", "E1"]
ZEBRA_CROSSING_ALL_CODES = ZEBRA_CROSSING_LEFT_CODES + ZEBRA_CROSSING_RIGHT_CODES
DIRECTION_TOLERANCE = 20  # degrees tolerance for 180° difference

# Compiled regex pattern for extracting numeric part from number_code field
NUMBER_CODE_PATTERN = re.compile(r"^(\d+)")

# Code transformation configuration constants
INVALID_CODES = {"x", "not classified", "k06", "931-1"}  # Codes that should be filtered out (case insensitive)

# Direct code-to-code replacement mappings
CODE_REPLACEMENTS = {
    "331": "3311",
    "373": "3732",
    "374": "3742",
    "411": "4111",
    "411_2": "4112",
    "413": "4131",
    "413_2": "4132",
    "413_3": "4133",
    "413_4": "4134",
    "413_5": "4135",
    "413_6": "4136",
    "414": "4141",
    "414_2": "4142",
    "414_4": "4144",
    "417": "4171",
    "417_2": "4172",
    "511": "5111",
    "511_2": "5112",
    "520_1": "5201",
    "521a": "52111",
    "521b": "52151",
    "521c": "52131",
    "531": "5311",
    "532": "5321",
    "533": "5331",
    "541a": "5411",
    "541b": "5412",
    "542b": "5422",
    "543a": "5431",
    "551": "5511",
    "551_2": "5512",
    "571": "5711",
    "572": "5721",
    "622": "6221",
    "623_2": "62324",
    "650": "6501",
    "650_2": "6502",
    "650_3": "6504",
    "651": "6511",
    "651_2": "6512",
    "681": "833S",
    "681_2": "831S",
    "681_3": "832S",
    "681_4": "834S",
    "681_5": "841S",
    "681_8": "6818",
    "681_9": "6819",
    "821": "821K",
    "823": "823K",
    "861b": "H22.2_6",
    "863": "8631",
    "871": "87111",
    "871_5": "87115",
    "872": "8722K",
    "872_2": "8714K",
    "E4.3_4": "E4.3_3_2_1",
    "H11S": "H11.1",
    "H12.8_2": "H12.8",
    "H12.10_4": "H12.10_2_2",
    "H19.2_2S": "H19.2_2",
    "H19.2_3S": "H19.2_3",
    "H19.2_4S": "H19.2_4",
    "H20.1": "H20_4",
    "H20.1S": "H20_4S",
}

# Codes that require color-based suffix (K for color=2, S for color=1)
COLOR_DEPENDENT_CODES = {
    "814",
    "815",
    "824",
    "825",
    "826",
    "828",
    "831",
    "832",
    "833",
    "834",
    "836",
    "843",
    "851",
    "852",
    "853",
    "H12.10_4_2",
}

# Codes that should get a default suffix if color field is missing from CSV.
# Maps code -> default suffix character (e.g. 'K' or 'S').
COLOR_CODES_DEFAULT_SUFFIX = {"824": "K", "825": "K", "826": "K", "828": "K", "843": "S"}

# Codes that require both code mapping AND color-based suffix
# Format: old_code -> {"new_code": "replacement", "color_1_suffix": "S/K/None", "color_2_suffix": "S/K/None"}
# If suffix is None, no suffix is added for that color value
CODE_AND_COLOR_DEPENDENT_CODES = {
    "H19_3": {"new_code": "H19.1_2", "color_1_suffix": "S", "color_2_suffix": None},
    "853_2": {"new_code": "8531", "color_1_suffix": "S", "color_2_suffix": "K"},
    "854": {"new_code": "8541", "color_1_suffix": "S", "color_2_suffix": "K"},
    "854_2": {"new_code": "8543", "color_1_suffix": "S", "color_2_suffix": "K"},
    "855a": {"new_code": "8552", "color_1_suffix": "S", "color_2_suffix": "K"},
    "855b": {"new_code": "8552", "color_1_suffix": "S", "color_2_suffix": "K"},
    "856a": {"new_code": "8561", "color_1_suffix": "S", "color_2_suffix": "K"},
    "856b": {"new_code": "8561", "color_1_suffix": "S", "color_2_suffix": "K"},
    "H12.10_2": {"new_code": "H12.10_2_2", "color_1_suffix": "S", "color_2_suffix": None},
    "H12.10_4": {"new_code": "H12.10_2_2", "color_1_suffix": "S", "color_2_suffix": None},
    "H12.2_2": {"new_code": "H12.2_2_2", "color_1_suffix": "S", "color_2_suffix": "K"},
    # Codes with conditional suffix only (no code mapping)
    "827": {"new_code": "827", "color_1_suffix": "S", "color_2_suffix": None},
    "845": {"new_code": "845", "color_1_suffix": None, "color_2_suffix": "K"},
    "833_2": {"new_code": "833_2", "color_1_suffix": "S", "color_2_suffix": None},
}

# Codes that should be replaced with validation against number_code field
# Format: old_code -> {"expected_number": "value", "new_code": "replacement"}
NUMBER_CODE_DEPENDENT_CODES = {
    "344_12": {"expected_number": "12", "new_code": "344"},
    "344_30": {"expected_number": "30", "new_code": "344"},
    "344_6": {"expected_number": "6", "new_code": "344"},
    "344_8": {"expected_number": "8", "new_code": "344"},
    "345_60": {"expected_number": "60", "new_code": "345"},
    "346_10": {"expected_number": "10", "new_code": "346"},
    "346_8": {"expected_number": "8", "new_code": "346"},
    "347_16": {"expected_number": "16", "new_code": "347"},
    "347_18": {"expected_number": "18", "new_code": "347"},
    "347_21": {"expected_number": "21", "new_code": "347"},
    "361_10": {"expected_number": "10", "new_code": "361"},
    "361_20": {"expected_number": "20", "new_code": "3619"},
    "361_30": {"expected_number": "30", "new_code": "3617"},
    "361_40": {"expected_number": "40", "new_code": "3618"},
    "361_5": {"expected_number": "5", "new_code": "361"},
    "361_50": {"expected_number": "50", "new_code": "3611"},
    "361_60": {"expected_number": "60", "new_code": "3612"},
    "361_70": {"expected_number": "70", "new_code": "3613"},
    "361_80": {"expected_number": "80", "new_code": "3614"},
    "362_20": {"expected_number": "20", "new_code": "362"},
    "362_30": {"expected_number": "30", "new_code": "3622"},
    "363_20": {"expected_number": "20", "new_code": "3637"},
    "363_30": {"expected_number": "30", "new_code": "3634"},
    "363_40": {"expected_number": "40", "new_code": "3635"},
    "364_20": {"expected_number": "20", "new_code": "3647"},
    "364_30": {"expected_number": "30", "new_code": "3644"},
    "364_40": {"expected_number": "40", "new_code": "3646"},
}

# Conditional code replacements based on number_code value
# Format: code -> {number_value: new_code}
# Only replaces if number_code matches a key, otherwise code stays unchanged
CONDITIONAL_NUMBER_CODE_REPLACEMENTS = {
    "363": {"40": "3635"},
}

# Enrichment texts for internal_additional_info field based on device type code
INTERNAL_ADDITIONAL_INFO_ENRICHMENTS = {
    "833S": "lisäksi voi olla lisäkilpi 832S linja-auto",
    "831S": "voi olla lisäkilpi 834S pakettiauto tai 833S kuorma-auto",
    "832S": "tai merkki 5411 linja-autokaista",
    "834S": "tai lisäkilpi 833S kuorma-auto",
    "6819": "tai lisäkilpi 843S polkupyörä",
}

# Codes that should have location_specifier = 4
LOCATION_SPECIFIER_4_CODES = ["4171", "4172", "418", "D3.1", "D3.1_2", "D3.2", "D3.2_2", "D3.3", "D3.3_2"]

# Codes that should that are valid but should be skipped
SKIPPABLE_CODES = ["6", "7"]

# allowed color values
ALLOWED_COLOR_VALUES = ["1", "2"]


class CSVHeadersV2:
    """CSV headers for new traffic sign data format with status field"""

    id = "id"
    attachment_url = "ssurl"
    code = "merkkikoodi"
    color = "taustaväri"
    condition = "merkin_ehto"
    coord_x = "x"
    coord_y = "y"
    coord_z = "z"
    direction = "atsimuutti"
    height = "korkeus"
    mount_id = "kiinnityskohta_id"
    mount_type = "tyyppi"
    number_code = "numerokoodi"
    parent_sign_id = "lisäkilven_päämerkin_id"
    scanned_at = "tallennusajankohta"
    sign_mount_type = "kiinnitys"
    status = "status"  # New field
    txt = "teksti"
    location_specifier = "sijaintitarkenne"

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional

HELSINKI_LONGITUDE = 2776957.204335059
HELSINKI_LATITUDE = 8442622.403718097

# Ticket machine device type codes - these additional signs can have null parent
TICKET_MACHINE_CODES = ["H20.91", "H20.92", "H20.93", "8591", "8592", "8593"]

# Signpost device type codes - traffic signs that should be migrated to signpost tables
SIGNPOST_CODES = [
    "6211",
    "6221",
    "62311",
    "62312",
    "62315",
    "62316",
    "62321",
    "62324",
    "6501",
    "6502",
    "6504",
    "6511",
    "6512",
    "6513",
    "6514",
    "6521",
    "6522",
    "6523",
    "6524",
    "F24.1",
    "F24.2",
    "F24.2_2",
    "F24.3",
    "F24.31",
    "F7.2",
    "F8.1",
    "F8.1_2",
]


@dataclass(frozen=True)
class SignValueFamily:
    """Traffic sign device type code family consisting of a generic code and its subcodes.

    Attributes:
        generic_code (str): Code of the generic device type, e.g. "C21".
        default_value (Optional[Decimal]): Value the generic device type carries by default.
        subcodes (Dict[str, Decimal]): Mapping of subcode to the value it is expected to have.
    """

    generic_code: str
    default_value: Optional[Decimal]
    subcodes: Dict[str, Decimal]


# Traffic sign code families used by the `check_traffic_sign_real_values` management command.
# Signs using a subcode must have exactly the value defined for that subcode. Signs using the generic
# code must not have a value that belongs to any of the family's subcodes.
TRAFFIC_SIGN_VALUE_FAMILIES: Dict[str, SignValueFamily] = {
    "C21": SignValueFamily(
        generic_code="C21",
        default_value=Decimal("2.2"),
        subcodes={
            "C21_2": Decimal("2.0"),
            "C21_3": Decimal("2.1"),
            "C21_4": Decimal("2.3"),
            "C21_5": Decimal("2.4"),
            "C21_6": Decimal("2.5"),
        },
    ),
    "C22": SignValueFamily(
        generic_code="C22",
        default_value=Decimal("3.0"),
        subcodes={
            "C22_2": Decimal("2.0"),
            "C22_3": Decimal("2.1"),
            "C22_4": Decimal("2.2"),
            "C22_5": Decimal("2.3"),
            "C22_6": Decimal("2.4"),
            "C22_7": Decimal("2.5"),
            "C22_8": Decimal("2.6"),
            "C22_9": Decimal("2.7"),
            "C22_10": Decimal("2.8"),
            "C22_11": Decimal("2.9"),
            "C22_12": Decimal("3.0"),
            "C22_13": Decimal("3.1"),
            "C22_14": Decimal("3.2"),
            "C22_15": Decimal("3.3"),
            "C22_16": Decimal("3.4"),
            "C22_17": Decimal("3.6"),
            "C22_18": Decimal("3.7"),
            "C22_19": Decimal("3.8"),
            "C22_20": Decimal("3.9"),
            "C22_21": Decimal("4.0"),
            "C22_22": Decimal("4.1"),
            "C22_23": Decimal("4.2"),
            "C22_24": Decimal("4.3"),
            "C22_25": Decimal("4.4"),
        },
    ),
    "C23": SignValueFamily(
        generic_code="C23",
        default_value=Decimal("20"),
        subcodes={
            "C23_2": Decimal("10"),
            "C23_3": Decimal("12"),
            "C23_4": Decimal("14"),
            "C23_5": Decimal("16"),
            "C23_6": Decimal("18"),
            "C23_7": Decimal("22"),
            "C23_8": Decimal("24"),
        },
    ),
    "C24": SignValueFamily(
        generic_code="C24",
        default_value=Decimal("12"),
        subcodes={
            "C24_2": Decimal("3.5"),
            "C24_3": Decimal("4"),
            "C24_4": Decimal("6"),
            "C24_5": Decimal("8"),
            "C24_6": Decimal("10"),
            "C24_7": Decimal("14"),
            "C24_8": Decimal("16"),
            "C24_9": Decimal("18"),
            "C24_10": Decimal("20"),
            "C24_11": Decimal("25"),
            "C24_12": Decimal("30"),
            "C24_13": Decimal("35"),
            "C24_14": Decimal("42"),
        },
    ),
    "C25": SignValueFamily(
        generic_code="C25",
        default_value=Decimal("30"),
        subcodes={
            "C25_2": Decimal("35"),
            "C25_3": Decimal("40"),
            "C25_4": Decimal("45"),
            "C25_5": Decimal("50"),
            "C25_6": Decimal("55"),
            "C25_7": Decimal("60"),
            "C25_8": Decimal("65"),
            "C25_9": Decimal("70"),
            "C25_10": Decimal("76"),
        },
    ),
    "C26": SignValueFamily(
        generic_code="C26",
        default_value=Decimal("8"),
        subcodes={
            "C26_2": Decimal("4"),
            "C26_3": Decimal("5"),
            "C26_4": Decimal("6"),
            "C26_5": Decimal("7"),
            "C26_6": Decimal("9"),
            "C26_7": Decimal("10"),
        },
    ),
    "C27": SignValueFamily(
        generic_code="C27",
        default_value=Decimal("14"),
        subcodes={
            "C27_2": Decimal("18"),
            "C27_3": Decimal("21"),
        },
    ),
    "D10": SignValueFamily(
        generic_code="D10",
        default_value=Decimal("50"),
        subcodes={
            "D10_2": Decimal("60"),
            "D10_3": Decimal("70"),
            "D10_4": Decimal("80"),
        },
    ),
    "D11": SignValueFamily(
        generic_code="D11",
        default_value=Decimal("50"),
        subcodes={
            "D11_2": Decimal("60"),
            "D11_3": Decimal("70"),
            "D11_4": Decimal("80"),
        },
    ),
    "A3.1": SignValueFamily(
        generic_code="A3.1",
        default_value=None,
        subcodes={
            "A3.1_2": Decimal("7"),
            "A3.1_3": Decimal("8"),
            "A3.1_4": Decimal("9"),
            "A3.1_5": Decimal("10"),
            "A3.1_6": Decimal("11"),
            "A3.1_7": Decimal("12"),
            "A3.1_8": Decimal("13"),
        },
    ),
    "A3.2": SignValueFamily(
        generic_code="A3.2",
        default_value=None,
        subcodes={
            "A3.2_2": Decimal("7"),
            "A3.2_3": Decimal("8"),
            "A3.2_4": Decimal("9"),
            "A3.2_5": Decimal("10"),
            "A3.2_6": Decimal("11"),
            "A3.2_7": Decimal("12"),
            "A3.2_8": Decimal("13"),
        },
    ),
    "C32": SignValueFamily(
        generic_code="C32",
        default_value=Decimal("60"),
        subcodes={
            "C32_2": Decimal("20"),
            "C32_3": Decimal("30"),
            "C32_4": Decimal("40"),
            "C32_5": Decimal("50"),
            "C32_6": Decimal("70"),
            "C32_7": Decimal("80"),
            "C32_8": Decimal("100"),
            "C32_9": Decimal("120"),
        },
    ),
    "C33": SignValueFamily(
        generic_code="C33",
        default_value=Decimal("40"),
        subcodes={
            "C33_2": Decimal("20"),
            "C33_3": Decimal("30"),
            "C33_4": Decimal("50"),
            "C33_5": Decimal("60"),
            "C33_6": Decimal("70"),
        },
    ),
    "C34": SignValueFamily(
        generic_code="C34",
        default_value=Decimal("40"),
        subcodes={
            "C34_2": Decimal("30"),
            "C34_3": Decimal("50"),
            "C34_4": Decimal("20"),
        },
    ),
    "C34p": SignValueFamily(
        generic_code="C34p",
        default_value=Decimal("40"),
        subcodes={
            "C34_2p": Decimal("30"),
            "C34_3p": Decimal("50"),
        },
    ),
    "C35": SignValueFamily(
        generic_code="C35",
        default_value=Decimal("40"),
        subcodes={
            "C35_2": Decimal("30"),
            "C35_3": Decimal("50"),
        },
    ),
    "C35p": SignValueFamily(
        generic_code="C35p",
        default_value=Decimal("40"),
        subcodes={
            "C35_2p": Decimal("30"),
            "C35_3p": Decimal("50"),
        },
    ),
    "361": SignValueFamily(
        generic_code="361",
        default_value=None,
        subcodes={
            "3611": Decimal("50"),
            "3612": Decimal("60"),
            "3613": Decimal("70"),
            "3614": Decimal("80"),
            "3615": Decimal("100"),
            "3616": Decimal("120"),
            "3617": Decimal("30"),
            "3618": Decimal("40"),
            "3619": Decimal("20"),
        },
    ),
    "362": SignValueFamily(
        generic_code="362",
        default_value=None,
        subcodes={
            "3621": Decimal("50"),
            "3622": Decimal("30"),
            "3623": Decimal("40"),
        },
    ),
    "363": SignValueFamily(
        generic_code="363",
        default_value=None,
        subcodes={
            "3633": Decimal("30"),
            "3634": Decimal("30"),
            "3635": Decimal("40"),
            "3636": Decimal("40"),
            "3637": Decimal("20"),
        },
    ),
    "364": SignValueFamily(
        generic_code="364",
        default_value=None,
        subcodes={
            "3643": Decimal("30"),
            "3644": Decimal("30"),
            "3645": Decimal("40"),
            "3646": Decimal("40"),
            "3647": Decimal("20"),
        },
    ),
}

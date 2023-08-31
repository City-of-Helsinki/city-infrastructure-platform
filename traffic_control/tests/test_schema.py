from enumfields import Enum

from traffic_control.schema import process_enum_values


class NumericEnum(Enum):
    ONE = 1
    TWO = 2
    THREE = 3


class StringEnum(Enum):
    FIRST = "A"
    SECOND = "B"
    THIRD = "C"


def test__process_enum_values__enum_choices_are_correct_type_and_sorted():
    schema_input = {
        "paths": {
            "/path/": {
                "get": {
                    "parameters": [
                        {
                            "in": "query",
                            "name": "numeric",
                            "schema": {
                                "enum": [
                                    NumericEnum.THREE,
                                    NumericEnum.ONE,
                                    NumericEnum.TWO,
                                ],
                            },
                        },
                        {
                            "in": "query",
                            "name": "size",
                            "schema": {
                                "enum": [
                                    StringEnum.SECOND,
                                    StringEnum.THIRD,
                                    StringEnum.FIRST,
                                ],
                            },
                        },
                        {
                            "in": "query",
                            "name": "other",
                            "schema": {
                                "enum": [
                                    "Y",
                                    "X",
                                    "Z",
                                ],
                            },
                        },
                    ],
                }
            }
        },
    }

    schema_expected = {
        "paths": {
            "/path/": {
                "get": {
                    "parameters": [
                        {
                            "in": "query",
                            "name": "numeric",
                            "schema": {
                                "enum": [
                                    1,
                                    2,
                                    3,
                                ],
                            },
                        },
                        {
                            "in": "query",
                            "name": "size",
                            "schema": {
                                "enum": [
                                    "A",
                                    "B",
                                    "C",
                                ],
                            },
                        },
                        {
                            "in": "query",
                            "name": "other",
                            "schema": {
                                "enum": [
                                    "Y",
                                    "X",
                                    "Z",
                                ],
                            },
                        },
                    ],
                }
            }
        },
    }

    assert process_enum_values(None, None, None, schema_input) == schema_expected

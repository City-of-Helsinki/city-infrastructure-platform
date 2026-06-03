"""Code transformation pipeline mixin for TrafficSignAnalyzerV2."""

from .traffic_sign_data_v2_constants import (
    ALLOWED_COLOR_VALUES,
    CODE_AND_COLOR_DEPENDENT_CODES,
    CODE_REPLACEMENTS,
    COLOR_CODES_DEFAULT_SUFFIX,
    COLOR_DEPENDENT_CODES,
    CONDITIONAL_NUMBER_CODE_REPLACEMENTS,
    CSVHeadersV2,
    INTERNAL_ADDITIONAL_INFO_ENRICHMENTS,
    INVALID_CODES,
    LOCATION_SPECIFIER_4_CODES,
    NUMBER_CODE_DEPENDENT_CODES,
    NUMBER_CODE_PATTERN,
    SKIPPABLE_CODES,
)


class CodeTransformMixin:
    """Mixin providing sign code filtering and enrichment pipeline methods.

    For a full description of all code transformation rules, replacement mappings,
    and enrichment logic applied by this mixin, see:
    docs/traffic_sign_import_v2_code_transformations.md
    """

    def _record_filtered_sign(self, row: dict, code: str, reason: str) -> None:
        """Append a filtered-out sign entry to the filtered_signs list.

        Args:
            row (dict): CSV row dictionary.
            code (str): The device type code that was filtered.
            reason (str): Reason the sign was filtered out.
        """
        self.filtered_signs.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "code": code,
                "reason": reason,
                "csv_row": self._row_to_csv_line(row, self.delimiter),
            }
        )

    def _apply_direct_code_replacement(self, row: dict) -> None:
        """Apply direct code-to-code replacement if applicable.

        Args:
            row (dict): CSV row dictionary (modified in place).
        """
        code = row.get(CSVHeadersV2.code, "")
        if code not in CODE_REPLACEMENTS:
            return
        new_code = CODE_REPLACEMENTS[code]
        self.code_replacements.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": new_code,
                "replacement_type": "direct_mapping",
            }
        )
        row[CSVHeadersV2.code] = new_code

    def _record_color_replacement_failure(self, row: dict, code: str, reason: str, color_value: str) -> None:
        """Append a color replacement failure entry to the failures list.

        Args:
            row (dict): CSV row dictionary.
            code (str): The device type code that failed replacement.
            reason (str): Failure reason string.
            color_value (str): The color value that caused the failure.
        """
        self.code_replacement_failures.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "code": code,
                "reason": reason,
                "color_value": color_value,
                "csv_row": self._row_to_csv_line(row, self.delimiter),
            }
        )

    def _record_number_code_failure(
        self,
        row: dict,
        code: str,
        expected_number: str,
        actual_number_code: str,
        cleaned_number: str,
        expected_replacement: str,
    ) -> None:
        """Append a number-code replacement failure entry to the failures list.

        Args:
            row (dict): CSV row dictionary.
            code (str): The device type code that failed replacement.
            expected_number (str): The number that was expected.
            actual_number_code (str): The actual number_code value (or extraction description).
            cleaned_number (str): The cleaned/extracted number that was found.
            expected_replacement (str): The replacement code that would have been applied.
        """
        self.code_replacement_failures.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "code": code,
                "reason": "number_code_mismatch",
                "expected_number": expected_number,
                "actual_number_code": actual_number_code,
                "cleaned_number": cleaned_number,
                "expected_replacement": expected_replacement,
                "csv_row": self._row_to_csv_line(row, self.delimiter),
            }
        )

    def _apply_color_based_suffix_no_color(self, row: dict, code: str, default_suffix: str | None) -> None:
        """Handle color-based suffix when the color field is absent.

        Args:
            row (dict): CSV row dictionary (modified in place).
            code (str): Current device type code.
            default_suffix (str | None): Default suffix to apply, or None if no default.
        """
        if not default_suffix:
            self._record_color_replacement_failure(row, code, "missing_color_field", "")
            return
        new_code = f"{code}{default_suffix}"
        self.code_replacements.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": new_code,
                "replacement_type": "color_based_default",
                "color_value": f"default_{default_suffix}",
            }
        )
        row[CSVHeadersV2.code] = new_code

    def _apply_color_suffix_with_valid_color(self, row: dict, code: str, color_value: str) -> None:
        """Record and apply a color-based suffix replacement for a valid color value.

        Args:
            row (dict): CSV row dictionary (modified in place).
            code (str): Original device type code.
            color_value (str): Validated color value ('1' or '2').
        """
        if color_value not in ALLOWED_COLOR_VALUES:
            self._record_color_replacement_failure(row, code, "invalid_color_value", color_value)
            return
        suffix = "S" if color_value == "1" else "K"
        new_code = f"{code}{suffix}"
        self.code_replacements.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": new_code,
                "replacement_type": "color_based",
                "color_value": color_value,
            }
        )
        row[CSVHeadersV2.code] = new_code

    def _apply_color_based_suffix(self, row: dict) -> None:
        """Apply color-based suffix transformation if applicable.

        Args:
            row (dict): CSV row dictionary (modified in place).
        """
        code = row.get(CSVHeadersV2.code, "")
        if code not in COLOR_DEPENDENT_CODES:
            return
        color_value = row.get(CSVHeadersV2.color, "")
        default_suffix = COLOR_CODES_DEFAULT_SUFFIX.get(code)
        if not color_value:
            self._apply_color_based_suffix_no_color(row, code, default_suffix)
            return
        self._apply_color_suffix_with_valid_color(row, code, color_value)

    def _apply_code_and_color_no_color(self, row: dict, code: str, base_code: str, config: dict) -> None:
        """Handle code and color transformation when color field is absent.

        Args:
            row (dict): CSV row dictionary (modified in place).
            code (str): Original device type code.
            base_code (str): Replacement base code from config.
            config (dict): Configuration dict with color_1_suffix and color_2_suffix.
        """
        if config["color_1_suffix"] is not None and config["color_2_suffix"] is not None:
            self._record_color_replacement_failure(row, code, "missing_color_field", "missing")
            return
        self.code_replacements.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": base_code,
                "replacement_type": "code_and_color_based_no_color",
                "color_value": "missing",
                "base_code": base_code,
                "suffix": "none",
            }
        )
        row[CSVHeadersV2.code] = base_code

    def _apply_code_and_color_with_valid_color(
        self, row: dict, code: str, base_code: str, config: dict, color_value: str
    ) -> None:
        """Record and apply a code-and-color replacement for a valid color value.

        Args:
            row (dict): CSV row dictionary (modified in place).
            code (str): Original device type code.
            base_code (str): Replacement base code from config.
            config (dict): Config dict with color_1_suffix and color_2_suffix.
            color_value (str): Validated color value ('1' or '2').
        """
        if color_value not in ["1", "2"]:
            self._record_color_replacement_failure(row, code, "invalid_color_value", color_value)
            return
        suffix = config["color_1_suffix"] if color_value == "1" else config["color_2_suffix"]
        new_code = f"{base_code}{suffix}" if suffix else base_code
        self.code_replacements.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": new_code,
                "replacement_type": "code_and_color_based",
                "color_value": color_value,
                "base_code": base_code,
                "suffix": suffix if suffix else "none",
            }
        )
        row[CSVHeadersV2.code] = new_code

    def _apply_code_and_color_transformation(self, row: dict) -> None:
        """Apply code mapping with color-based suffix transformation if applicable.

        Args:
            row (dict): CSV row dictionary (modified in place).
        """
        code = row.get(CSVHeadersV2.code, "")
        if code not in CODE_AND_COLOR_DEPENDENT_CODES:
            return
        config = CODE_AND_COLOR_DEPENDENT_CODES[code]
        base_code = config["new_code"]
        color_value = row.get(CSVHeadersV2.color, "")
        if not color_value:
            self._apply_code_and_color_no_color(row, code, base_code, config)
            return
        self._apply_code_and_color_with_valid_color(row, code, base_code, config, color_value)

    def _apply_number_code_from_code_extraction(
        self, row: dict, code: str, expected_number: str, replacement_code: str
    ) -> None:
        """Extract number from code pattern and validate for number code replacement.

        Args:
            row (dict): CSV row dictionary (modified in place).
            code (str): Original device type code.
            expected_number (str): Expected number value to validate against.
            replacement_code (str): Replacement code if validation passes.
        """
        code_parts = code.split("_")
        if len(code_parts) <= 1:
            self._record_number_code_failure(
                row,
                code,
                expected_number,
                "(no number_code field, extraction failed: no underscore in code)",
                "",
                replacement_code,
            )
            return
        extracted_number = code_parts[-1]
        if extracted_number != expected_number:
            self._record_number_code_failure(
                row,
                code,
                expected_number,
                f"(no number_code field, extracted from code: {extracted_number})",
                extracted_number,
                replacement_code,
            )
            return
        self.code_replacements.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": replacement_code,
                "replacement_type": "number_code_based",
                "number_code_value": f"(extracted from code: {extracted_number})",
                "validated_number": expected_number,
            }
        )
        row[CSVHeadersV2.code] = replacement_code
        row[CSVHeadersV2.number_code] = expected_number

    def _apply_number_code_replacement(
        self, row: dict, code: str, replacement_code: str, number_code_value: str, expected_number: str
    ) -> None:
        """Validate the cleaned number and apply or reject the number-code replacement.

        Args:
            row (dict): CSV row dictionary (modified in place).
            code (str): Original device type code.
            replacement_code (str): Target code to replace with if valid.
            number_code_value (str): Raw number_code field value from the CSV row.
            expected_number (str): The number string that must match for replacement to occur.
        """
        match = NUMBER_CODE_PATTERN.match(number_code_value)
        cleaned_number = match.group(1) if match else ""
        if cleaned_number != expected_number:
            self._record_number_code_failure(
                row, code, expected_number, number_code_value, cleaned_number, replacement_code
            )
            return
        self.code_replacements.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": replacement_code,
                "replacement_type": "number_code_based",
                "number_code_value": number_code_value,
                "validated_number": expected_number,
            }
        )
        row[CSVHeadersV2.code] = replacement_code
        row[CSVHeadersV2.number_code] = expected_number

    def _apply_number_code_validation(self, row: dict) -> None:
        """Apply number-code based validation and replacement if applicable.

        Args:
            row (dict): CSV row dictionary (modified in place).
        """
        code = row.get(CSVHeadersV2.code, "")
        if code not in NUMBER_CODE_DEPENDENT_CODES:
            return
        config = NUMBER_CODE_DEPENDENT_CODES[code]
        expected_number = config["expected_number"]
        replacement_code = config["new_code"]
        number_code_value = row.get(CSVHeadersV2.number_code, "")
        if not number_code_value:
            self._apply_number_code_from_code_extraction(row, code, expected_number, replacement_code)
            return
        self._apply_number_code_replacement(row, code, replacement_code, number_code_value, expected_number)

    def _apply_conditional_number_code_replacement(self, row: dict) -> None:
        """Apply conditional code replacement based on number_code value.

        Args:
            row (dict): CSV row dictionary (modified in place).
        """
        code = row.get(CSVHeadersV2.code, "")
        if code not in CONDITIONAL_NUMBER_CODE_REPLACEMENTS:
            return
        number_code_value = row.get(CSVHeadersV2.number_code, "")
        match = NUMBER_CODE_PATTERN.match(number_code_value) if number_code_value else None
        cleaned_number = match.group(1) if match else ""
        replacements = CONDITIONAL_NUMBER_CODE_REPLACEMENTS[code]
        if cleaned_number not in replacements:
            return
        new_code = replacements[cleaned_number]
        self.code_replacements.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": new_code,
                "replacement_type": "conditional_number_code",
            }
        )
        row[CSVHeadersV2.code] = new_code

    def _enrich_location_specifier(self, row: dict) -> None:
        """Add location_specifier value if applicable.

        Args:
            row (dict): CSV row dictionary (modified in place).
        """
        code = row.get(CSVHeadersV2.code, "")
        location_specifier_value = row.get(CSVHeadersV2.location_specifier, "")
        if not location_specifier_value and code in LOCATION_SPECIFIER_4_CODES:
            self.enriched_signs.append(
                {
                    "source_id": row.get(CSVHeadersV2.id),
                    "code": code,
                    "field": "location_specifier",
                    "old_value": None,
                    "new_value": "4",
                }
            )
            row[CSVHeadersV2.location_specifier] = "4"

    def _enrich_internal_additional_info(self, row: dict) -> None:
        """Enrich internal_additional_info field for specific device type codes.

        Args:
            row (dict): CSV row dictionary (modified in place).
        """
        code = row.get(CSVHeadersV2.code, "")
        if code not in INTERNAL_ADDITIONAL_INFO_ENRICHMENTS:
            return
        value = INTERNAL_ADDITIONAL_INFO_ENRICHMENTS[code]
        self.enriched_signs.append(
            {
                "source_id": row.get(CSVHeadersV2.id),
                "code": code,
                "field": "internal_additional_info",
                "old_value": None,
                "new_value": value,
            }
        )
        row["internal_additional_info"] = value

    @staticmethod
    def _is_skippable_code(code: str) -> bool:
        return code in SKIPPABLE_CODES

    def _filter_and_enrich_sign_rows(self, sign_rows: list[dict]) -> list[dict]:
        """Filter out invalid sign codes, replace device type codes, and add location_specifier values.

        Applies the full transformation pipeline in order: invalid-code filtering,
        direct code replacement, color-based suffix, code+color transformation,
        number-code validation, conditional number-code replacement, skippable-code
        filtering, location_specifier enrichment, and internal_additional_info enrichment.

        See docs/traffic_sign_import_v2_code_transformations.md for the complete
        specification of all transformation rules.

        Args:
            sign_rows (list[dict]): List of sign row dictionaries.

        Returns:
            list[dict]: Filtered and enriched list of sign row dictionaries.
        """
        processed_rows = []
        for row in sign_rows:
            code = row.get(CSVHeadersV2.code, "")
            if code.lower() in INVALID_CODES:
                self._record_filtered_sign(row, code, "invalid_code")
                continue
            self._apply_direct_code_replacement(row)
            self._apply_color_based_suffix(row)
            self._apply_code_and_color_transformation(row)
            self._apply_number_code_validation(row)
            self._apply_conditional_number_code_replacement(row)
            code = row.get(CSVHeadersV2.code, "")
            if self._is_skippable_code(code):
                self._record_filtered_sign(row, code, "skipped_code")
                continue
            self._enrich_location_specifier(row)
            self._enrich_internal_additional_info(row)
            processed_rows.append(row)
        return processed_rows

    def _add_internal_status_to_rows(self, sign_rows: list[dict]) -> None:
        """Add internal_status column to each row based on database comparison.

        Args:
            sign_rows (list[dict]): List of sign row dictionaries (modified in place).
        """
        for row in sign_rows:
            source_id = row.get(CSVHeadersV2.id, "")
            code = row.get(CSVHeadersV2.code, "")
            if not source_id:
                row["internal_status"] = "new"
                continue
            is_additional = self._is_additional_sign(row)
            is_signpost = self._is_signpost(row)
            if is_additional:
                db_code = self.additional_sign_reals_by_source_id.get(source_id)
            elif is_signpost:
                db_code = self.signpost_reals_by_source_id.get(source_id)
            else:
                db_code = self.sign_reals_by_source_id.get(source_id)
            if db_code is None:
                row["internal_status"] = "new"
            elif db_code == code:
                row["internal_status"] = "unchanged"
            else:
                row["internal_status"] = "changed"

    @staticmethod
    def _add_internal_additional_info_to_rows(sign_rows: list[dict]) -> None:
        """Add internal_additional_info field to each row for future enrichment.

        Args:
            sign_rows (list[dict]): List of sign row dictionaries (modified in place).
        """
        for row in sign_rows:
            row["internal_additional_info"] = None

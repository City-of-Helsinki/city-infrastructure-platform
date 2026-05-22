# Traffic Sign Import V2 — Analysis Reports Reference
This document describes every report produced by `TrafficSignAnalyzerV2.analyze()`.
Reports are returned as a list of dicts, each with a `REPORT_TYPE` string key and a
`results` list.
Source files:
- `traffic_control/analyze_utils/traffic_sign_data_v2_reports.py`
- `traffic_control/analyze_utils/traffic_sign_data_v2_status_reports.py`
---
## Report categories
| # | Category | Reports |
|---|----------|---------|
| 1 | [CSV pre-processing](#1-csv-pre-processing) | 4 |
| 2 | [Status distribution](#2-status-distribution) | 2 |
| 3 | [Status records](#3-status-records) | 5 |
| 4 | [Non-existing mount references](#4-non-existing-mount-references) | 3 |
| 5 | [Mountless signs](#5-mountless-signs) | 3 |
| 6 | [Sign relationships](#6-sign-relationships) | 3 |
| 7 | [Distance](#7-distance) | 3 |
| 8 | [Duplicate detection](#8-duplicate-detection) | 3 |
| 9 | [Mount health](#9-mount-health) | 2 |
| 10 | [Validation](#10-validation) | 3 |
| 11 | [Missing from database](#11-missing-from-database) | 4 |
| 12 | [Found in database](#12-found-in-database) | 4 |
| 13 | [CSV-to-DB location distance](#13-csv-to-db-location-distance) | 4 |
---
## 1. CSV pre-processing
These four reports surface the side-effects of the code transformation pipeline.
See `traffic_sign_import_v2_code_transformations.md` for full pipeline details.
### `FILTERED SIGNS (REMOVED FROM CSV)`
Signs that were removed from the import because their `merkkikoodi` was in the
invalid-codes list (`x`, `not classified`, `k06`, `931-1`) or the skipped-codes
list (`6`, `7`).
**Result fields:** `source_id`, `code`, `reason` (`invalid_code` or `skipped_code`),
`csv_row`
---
### `ENRICHED SIGNS (LOCATION_SPECIFIER ADDED)`
Signs that had a field value automatically added by the enrichment pipeline.
Currently covers two enrichment types:
- **`location_specifier`**: set to `4` when the code is in `LOCATION_SPECIFIER_4_CODES`
  and the field was blank.
- **`internal_additional_info`**: set to a Finnish hint text when the code is in
  `INTERNAL_ADDITIONAL_INFO_ENRICHMENTS`.
**Result fields:** `source_id`, `code`, `field`, `old_value`, `new_value`
---
### `CODE REPLACEMENTS (DEVICE TYPE CODES UPDATED)`
All successful code transformations — direct replacements, color suffix additions,
code+color transformations, and number-code replacements.
**Result fields:** `source_id`, `old_code`, `new_code`, `replacement_type`,
plus type-specific extras (`color_value`, `number_code_value`, `suffix`, etc.)
---
### `CODE REPLACEMENT FAILURES (SANITY CHECK FAILURES)`
Cases where a conditional transformation could not be completed — missing or invalid
`taustaväri`, or `numerokoodi` not matching the expected value.
**Result fields:** `source_id`, `code`, `reason`, `color_value` / `actual_number_code`,
`csv_row`
---
## 2. Status distribution
### `STATUS DISTRIBUTION`
Counts and percentages of mounts, traffic signs, and additional signs broken down by
status value (`New`, `Unchanged`, `Changed`, `Removed`, `invalid`).
For signs, also includes a per-device-type-code breakdown.
**Result fields:** `object_type`, `status`, `count`, `percentage`, `code_breakdown`
---
### `INVALID STATUS VALUES`
Objects whose `status` field contains a value other than the four valid statuses
(`new`, `unchanged`, `changed`, `removed`, case-insensitive).
**Result fields:** `object_type`, `{mount|sign|additional_sign}_source_id`,
`invalid_status`
---
## 3. Status records
Each report lists all objects carrying that status, together with a comparison between
the CSV code and the database code (for signs and additional signs).
### `NEW RECORDS`
All signs/additional signs with `status = New`.
### `CHANGED RECORDS`
All signs/additional signs with `status = Changed`.
### `UNCHANGED RECORDS`
All signs/additional signs with `status = Unchanged`.
### `REMOVE RECORDS`
All objects (mounts, signs, additional signs, signposts) with `status = Removed`.
**Common result fields (signs/additional signs):** `object_type`, `source_id`,
`old_device_code` (from DB), `new_device_code` (from CSV), `old_legacy_code`,
`new_legacy_code`, `has_changed`
**Mounts and signposts in REMOVE RECORDS:** `object_type`,
`{mount|signpost}_source_id`
---
### `REMOVE WITH INVALID LOCATION`
Removed objects (any type) whose coordinates fail the geometry legitimacy check
(`geometry_is_legit`). These are locations that fall outside acceptable bounds for
the project SRID.
**Result fields:** `object_type`, `{type}_source_id`, `device_code` (signs only),
`location` (EWKT)
---
## 4. Non-existing mount references
Signs whose `kiinnityskohta_id` does not match any mount row in the mount CSV.
Indicates a data integrity issue — the sign references a mount that was not delivered.
### `NON EXISTING MOUNTS FOR ADDITIONAL SIGNS`
**Result fields:** `additional_sign_source_id`, `mount_source_id`, `devicetypecode`,
`status`, `internal_status`, `additional_sign_ssurl`, `mount_ssurl`
---
### `NON EXISTING MOUNTS FOR SIGNPOSTS`
**Result fields:** `signpost_source_id`, `mount_source_id`, `devicetypecode`, `status`,
`internal_status`, `csv_ssurl`, `mount_ssurl`
---
### `NON EXISTING MOUNTS FOR SIGNS`
**Result fields:** `sign_source_id`, `mount_source_id`, `devicetypecode`, `status`,
`internal_status`, `csv_ssurl`, `mount_ssurl`
---
## 5. Mountless signs
Signs where `kiinnityskohta_id` is blank, the referenced mount does not exist in the
CSV, or the referenced mount has `status = Removed`. Signs with `status = Removed`
are themselves excluded from these reports.
> **Relationship to Non-existing mount references:** A sign with a non-blank mount ID
> that is absent from the mount CSV will appear in **both** the non-existing mounts
> report (section 4) **and** the mountless report (this section). The mountless report
> additionally covers blank mount IDs and mounts that exist but are `Removed`.
### `MOUNTLESS ADDITIONAL SIGNS`
**Result fields:** `additional_sign_source_id`, `status`, `mount_status`
(`Removed` if mount exists but is removed, `"does not exist"` if not found in the mount CSV)
---
### `MOUNTLESS SIGNPOSTS`
**Result fields:** `signpost_source_id`, `status`, `mount_status`
---
### `MOUNTLESS SIGNS`
**Result fields:** `sign_source_id`, `status`, `mount_status`
---
## 6. Sign relationships
### `SIGNLESS ADDITIONAL SIGNS`
Additional signs where `lisäkilven_päämerkin_id` (parent sign ID) is blank.
Additional signs are expected to always reference a parent main sign.
**Result fields:** `additional_sign_source_id`, `old_device_code` (from DB),
`new_device_code` (from CSV), `status`, `internal_status`, `csv_ssurl`
---
### `MAIN SIGNS WITH PARENT`
Traffic signs (not additional signs) that have a non-empty `lisäkilven_päämerkin_id`.
Main signs are not expected to have a parent reference; this usually indicates
incorrect source data.
**Result fields:** `sign_source_id`, `sign_device_code`, `sign_status`,
`parent_source_id`, `parent_device_code`, `parent_type`
(`additional_sign` | `main_sign` | `not_found_in_csv`), `parent_status`
---
### `ACTIVE ADDITIONAL SIGNS WITH REMOVED PARENT`
Additional signs that are **not** marked as `Removed` but whose
`lisäkilven_päämerkin_id` references a traffic sign or signpost that **is** marked
as `Removed`. This indicates a data integrity issue — the parent has been decommissioned
but the child additional sign has not been updated accordingly.
Only parents found in the traffic signs CSV or signposts CSV are checked; additional
signs that reference another additional sign as parent are not covered here.
**Result fields:** `additional_sign_source_id`, `additional_sign_code`,
`additional_sign_status`, `parent_source_id`, `parent_code`, `parent_status`,
`parent_type` (`traffic_sign` | `signpost`), `additional_sign_ssurl`
---
## 7. Distance
### `MOUNT DISTANCES`
For every mount, lists distances (in project SRID units) from the mount point to each
attached sign and additional sign.
**Result fields:** `mount_source_id`, `distance` → `{ "signs": [...], "additional_signs": [...] }`
---
### `ADDITIONAL SIGN DISTANCES`
For every additional sign with a valid mount reference, lists distance to mount and
distance to the parent sign (if found).
**Result fields:** `additional_sign_source_id`, `sign_code`, `mount_source_id`,
`mount_type`, `distance_to_mount`, `parent_source_id`, `distance_to_parent`,
`parent_is_additional_sign`, `parent_code`, `status`, `link`
---
### `SIGN DISTANCES`
For every traffic sign that has a valid mount reference, lists the distance from the
sign to its mount.
**Result fields:** `sign_source_id`, `sign_code`, `mount_source_id`, `mount_type`,
`distance_to_mount`, `status`, `link`
---
## 8. Duplicate detection
### `DUPLICATE SIGNS ON SAME MOUNT`
Mounts that have two or more traffic signs whose `merkkikoodi` resolves to the **same
device type** (i.e. the same `TrafficControlDeviceType` record, matched by both `code`
and `legacy_code`).
Mounts with `status = Removed` are excluded. Signs with `status = Removed` are also
excluded from duplicate grouping.
**Excluded pairs:** A group of **exactly 2** signs where both signs share the **same**
code from the following list is silently excluded from the report, as these are
expected legitimate pairs (e.g. double-sided signs):
`5111`, `5112`, `E1`, `E1_2`, `5311`, `5331`, `E6`, `E7`
Groups of 3 or more signs with these codes, or pairs where the two signs have
*different* codes (even if both are on the excluded list), are still reported.
**Result fields:** `mount_source_id`, `mount_location` (EWKT),
`duplicate_signs` (list of `"source_id | code | status | direction"` strings)
---
### `DUPLICATE SIGNS ON SAME MOUNT (EXACT CODE)`
Same as above but matches on the **exact raw code string** rather than device type ID.
Catches identical codes that might share a device type with a different legacy code.
The same pair-exclusion logic applies (see above).
**Result fields:** same as above
---
### `ADDED DOUBLE SIDED ZEBRA CROSSINGS`
Mounts where two or more **New** zebra crossing signs face approximately opposite
directions (within ±20° of 180° apart).
Zebra crossing codes detected:
Left: `511`, `5112`, `E1_2` | Right: `5111`, `E1`
**Result fields:** `mount_source_id`, `sign_source_ids` (list of 2),
`codes_found` (list of 2), `directions` (list of 2 azimuths),
`direction_difference` (degrees), `status`
---
## 9. Mount health
### `MOUNTS WITHOUT ANY SIGNS`
Mounts from the CSV that have no traffic signs, additional signs, or signposts
attached to them.
**Result fields:** `mount_source_id`, `status`
---
### `MOUNTS WITH REMOVED SIGNS`
Mounts that have at least one attached sign or additional sign with `status = Removed`.
Helps identify mounts that may need physical inspection or removal.
**Result fields:** `mount_source_id`, `location` (EWKT),
`removed_signs_ssurls` (photo URLs for all removed signs on that mount)
---
## 10. Validation
### `TIMESTAMP FORMAT ERRORS`
Objects whose `tallennusajankohta` field cannot be parsed as
`%Y/%m/%d %H:%M:%S%z`. Empty timestamps are skipped.
**Result fields:** `object_type`, `{type}_source_id`, `invalid_timestamp`
---
### `INVALID DEVICE TYPE CODES`
Traffic signs and additional signs whose `merkkikoodi` (after all transformations) does
not match any `code` or `legacy_code` in the `TrafficControlDeviceType` table.
These signs will be skipped during import.
**Result fields:** `object_type`, `{sign|additional_sign}_source_id`, `invalid_code`,
`status`, `csv_row`
---
### `STATUS AND INTERNAL_STATUS MISMATCH`
Inconsistencies between the CSV-supplied `status` and the `internal_status` computed
by comparing the CSV code against the database.
| CSV status | Problematic `internal_status` | Meaning |
|------------|-------------------------------|---------|
| `New` | `unchanged` or `changed` | Claims new but already in DB |
| `Unchanged` | `new` | Claims unchanged but not in DB |
| `Unchanged` | `changed` | Claims unchanged but code differs |
| `Changed` | `new` | Claims changed but not in DB |
| `Changed` | `unchanged` | Claims changed but code matches |
| `Removed` | `new` | Claims removed but never in DB |
**Result fields:** `object_type`, `source_id`, `status`, `internal_status`,
`db_code`, `db_legacy_code`, `csv_code`, `csv_ssurl`, `mismatch_reason`
---
## 11. Missing from database
Objects with a non-`New` status (`Unchanged`, `Changed`, or `Removed`) that should
already exist in the database but do not.
Includes a `found_in_previous_csv` flag to distinguish objects seen in a prior import
file from genuinely new mismatches.
### `MISSING MOUNTS FROM DATABASE`
**Extra fields:** `mount_type`, `traffic_sign_codes`, `additional_sign_codes`,
`is_orphan` (mount has no attached signs), `found_in_previous_csv`
### `MISSING TRAFFIC SIGNS FROM DATABASE`
**Result fields:** `sign_source_id`, `status`, `device_code`, `found_in_previous_csv`,
`csv_ssurl`
### `MISSING ADDITIONAL SIGNS FROM DATABASE`
**Result fields:** `additional_sign_source_id`, `status`, `device_code`,
`found_in_previous_csv`
### `MISSING SIGNPOSTS FROM DATABASE`
**Result fields:** `signpost_source_id`, `status`, `device_code`,
`found_in_previous_csv`, `csv_ssurl`
---
## 12. Found in database
These four reports cross-reference every CSV object against the database and list the
ones that were found, with their DB primary key. Useful to verify that a previous
import ran correctly.
### `MOUNTS FOUND IN DATABASE`
**Result fields:** `source_id`, `db_id`, `status`
### `TRAFFIC SIGNS FOUND IN DATABASE`
**Result fields:** `source_id`, `db_id`, `status`
### `ADDITIONAL SIGNS FOUND IN DATABASE`
**Result fields:** `source_id`, `db_id`, `status`, `csv_ssurl`
### `SIGNPOSTS FOUND IN DATABASE`
**Result fields:** `source_id`, `db_id`, `status`, `csv_ssurl`
---
## 13. CSV-to-DB location distance
For every object present in **both** the CSV and the database, computes the Euclidean
distance between the CSV coordinates and the stored database location.
Only objects with a matching `source_id` in both sources are included.
### `MOUNT CSV TO DB LOCATION DISTANCE`
### `TRAFFIC SIGN CSV TO DB LOCATION DISTANCE`
### `ADDITIONAL SIGN CSV TO DB LOCATION DISTANCE`
### `SIGNPOST CSV TO DB LOCATION DISTANCE`
**Common result fields:** `source_id`, `db_id`, `status`, `csv_code`, `db_code`,
`csv_mount_type`, `db_mount_type`, `csv_x`, `csv_y`, `db_x`, `db_y`,
`distance` (project SRID units), `link` (CSV photo URL), `db_ssurl` (DB photo URL)

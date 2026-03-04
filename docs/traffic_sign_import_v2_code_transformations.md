# Traffic Sign Import V2 — Code Transformations Reference

This document describes every transformation applied to device type codes (`merkkikoodi`)
during CSV pre-processing in `TrafficSignAnalyzerV2`.
Source of truth: `traffic_control/analyze_utils/traffic_sign_data_v2_constants.py`

---

## Processing Pipeline Order

Each sign row passes through the following steps in order:

1. **Filter — invalid codes** (row removed entirely)
2. **Direct code replacement**
3. **Color-based suffix**
4. **Code + color transformation**
5. **Number-code validation**
6. **Conditional number-code replacement**
7. **Filter — skipped codes** (row removed after step 2–6 so replacements apply first)
8. **Enrich — `location_specifier`**
9. **Enrich — `internal_additional_info`**

---

## 1. Filtered / Ignored Codes

Rows whose `merkkikoodi` matches any of the following values (case-insensitive) are
**removed from all further processing and not imported**.

| Code | Reason |
|------|--------|
| `x` | Placeholder / unclassified |
| `not classified` | Unclassified |
| `k06` | Invalid code |
| `931-1` | Invalid code |

---

## 2. Skipped Codes (removed after transformations)

Rows with the following codes are removed **after** steps 2–6 have run.
This ensures that codes which map to a skipped value via a replacement are also caught.

| Code |
|------|
| `6` |
| `7` |

---

## 3. Direct Code Replacements

A straight one-to-one code swap. No conditions required.

| Old code | New code |
|----------|----------|
| `331` | `3311` |
| `373` | `3732` |
| `374` | `3742` |
| `411` | `4111` |
| `411_2` | `4112` |
| `413` | `4131` |
| `413_2` | `4132` |
| `413_3` | `4133` |
| `413_4` | `4134` |
| `413_5` | `4135` |
| `413_6` | `4136` |
| `414` | `4141` |
| `414_2` | `4142` |
| `414_4` | `4144` |
| `417` | `4171` |
| `417_2` | `4172` |
| `511` | `5111` |
| `511_2` | `5112` |
| `520_1` | `5201` |
| `521a` | `52111` |
| `521b` | `52151` |
| `521c` | `52131` |
| `531` | `5311` |
| `532` | `5321` |
| `533` | `5331` |
| `541a` | `5411` |
| `541b` | `5412` |
| `542b` | `5422` |
| `543a` | `5431` |
| `551` | `5511` |
| `551_2` | `5512` |
| `571` | `5711` |
| `572` | `5721` |
| `622` | `6221` |
| `623_2` | `62324` |
| `650` | `6501` |
| `650_2` | `6502` |
| `650_3` | `6504` |
| `651` | `6511` |
| `651_2` | `6512` |
| `681` | `833S` |
| `681_2` | `831S` |
| `681_3` | `832S` |
| `681_4` | `834S` |
| `681_5` | `841S` |
| `681_8` | `6818` |
| `681_9` | `6819` |
| `821` | `821K` |
| `823` | `823K` |
| `861b` | `H22.2_6` |
| `863` | `8631` |
| `871` | `87111` |
| `871_5` | `87115` |
| `872` | `8722K` |
| `872_2` | `8714K` |
| `E4.3_4` | `E4.3_3_2_1` |
| `H11S` | `H11.1` |
| `H12.8_2` | `H12.8` |
| `H12.10_4` | `H12.10_2_2` |
| `H19.2_2S` | `H19.2_2` |
| `H19.2_3S` | `H19.2_3` |
| `H19.2_4S` | `H19.2_4` |
| `H20.1` | `H20_4` |
| `H20.1S` | `H20_4S` |

---

## 4. Color-Based Suffix

For codes listed below, a suffix is appended based on the `taustaväri` (color) field:

- `taustaväri = 1` → suffix **`S`** (silver/white)
- `taustaväri = 2` → suffix **`K`** (yellow)

Result: `<code><suffix>` e.g. `814` + color `1` → `814S`

### Codes requiring color suffix

`814`, `815`, `824`, `825`, `826`, `828`, `831`, `832`, `833`, `834`, `836`, `843`,
`851`, `852`, `853`, `H12.10_4_2`

### Default suffix when color field is missing

Some codes have a defined fallback suffix applied when `taustaväri` is absent:

| Code | Default suffix | Result |
|------|---------------|--------|
| `824` | `K` | `824K` |
| `825` | `K` | `825K` |
| `826` | `K` | `826K` |
| `828` | `K` | `828K` |
| `843` | `S` | `843S` |

For all other color-dependent codes, a missing color field is recorded as a
**replacement failure** and the code is left unchanged.

### Error cases

| Condition | Outcome |
|-----------|---------|
| `taustaväri` absent and no default configured | Failure recorded; code unchanged |
| `taustaväri` present but not `1` or `2` | Failure recorded; code unchanged |

---

## 5. Code + Color Transformation

These codes require **both** a base code change **and** an optional color suffix.
The suffix rules are the same as above (`1` → `S`, `2` → `K`), but `None` means
no suffix is added for that color value.

| Old code | New base code | color=1 suffix | color=2 suffix | Notes |
|----------|--------------|----------------|----------------|-------|
| `H19_3` | `H19.1_2` | `S` | *(none)* | |
| `853_2` | `8531` | `S` | `K` | |
| `854` | `8541` | `S` | `K` | |
| `854_2` | `8543` | `S` | `K` | |
| `855a` | `8552` | `S` | `K` | |
| `855b` | `8552` | `S` | `K` | |
| `856a` | `8561` | `S` | `K` | |
| `856b` | `8561` | `S` | `K` | |
| `H12.10_2` | `H12.10_2_2` | `S` | *(none)* | |
| `H12.10_4` | `H12.10_2_2` | `S` | *(none)* | |
| `H12.2_2` | `H12.2_2_2` | `S` | `K` | |
| `827` | `827` | `S` | *(none)* | Suffix-only; no base code change |
| `845` | `845` | *(none)* | `K` | Suffix-only; no base code change |
| `833_2` | `833_2` | `S` | *(none)* | Suffix-only; no base code change |

When both suffixes are non-`None` and `taustaväri` is missing, a failure is recorded
and the code is left unchanged. When only one suffix is `None` and color is missing,
the base code replacement is applied without any suffix.

---

## 6. Number-Code Validation

These codes encode a speed/distance value in the code string itself (e.g. `361_50`).
The numeric part is validated against the `numerokoodi` CSV field before replacement.

**Validation steps:**

1. Read `numerokoodi` field and extract leading digits (regex `^\d+`).
2. If `numerokoodi` is empty, attempt extraction from the code string itself
   (last segment after `_`).
3. If the extracted number matches `expected_number`, apply `new_code`.
4. Otherwise, record a **replacement failure** and leave the code unchanged.

| Old code | Expected number | New code |
|----------|----------------|----------|
| `344_12` | `12` | `344` |
| `344_30` | `30` | `344` |
| `344_6` | `6` | `344` |
| `344_8` | `8` | `344` |
| `345_60` | `60` | `345` |
| `346_10` | `10` | `346` |
| `346_8` | `8` | `346` |
| `347_16` | `16` | `347` |
| `347_18` | `18` | `347` |
| `347_21` | `21` | `347` |
| `361_10` | `10` | `361` |
| `361_20` | `20` | `3619` |
| `361_30` | `30` | `3617` |
| `361_40` | `40` | `3618` |
| `361_5` | `5` | `361` |
| `361_50` | `50` | `3611` |
| `361_60` | `60` | `3612` |
| `361_70` | `70` | `3613` |
| `361_80` | `80` | `3614` |
| `362_20` | `20` | `362` |
| `362_30` | `30` | `3622` |
| `363_20` | `20` | `3637` |
| `363_30` | `30` | `3634` |
| `363_40` | `40` | `3635` |
| `364_20` | `20` | `3647` |
| `364_30` | `30` | `3644` |
| `364_40` | `40` | `3646` |

---

## 7. Conditional Number-Code Replacement

These codes are replaced **only when** `numerokoodi` matches a specific value.
If the value does not match, the code is left **unchanged** (no failure recorded).

| Code | `numerokoodi` value | New code |
|------|---------------------|----------|
| `363` | `40` | `3635` |

---

## 8. Enrichments (non-filtering)

### location_specifier

The following codes automatically receive `location_specifier = 4` if the field
is currently empty in the CSV row:

`4171`, `4172`, `418`, `D3.1`, `D3.1_2`, `D3.2`, `D3.2_2`, `D3.3`, `D3.3_2`

### internal_additional_info

The following final codes (post-replacement) receive a Finnish hint text in the
`internal_additional_info` field:

| Code | Text |
|------|------|
| `833S` | lisäksi voi olla lisäkilpi 832S linja-auto |
| `831S` | voi olla lisäkilpi 834S pakettiauto tai 833S kuorma-auto |
| `832S` | tai merkki 5411 linja-autokaista |
| `834S` | tai lisäkilpi 833S kuorma-auto |
| `6819` | tai lisäkilpi 843S polkupyörä |

---

## Replacement Failure Reporting

Any step that cannot complete a transformation records a failure entry in the
`CODE REPLACEMENT FAILURES (SANITY CHECK FAILURES)` report with the following fields:

| Field | Description |
|-------|-------------|
| `source_id` | Sign source ID from CSV |
| `code` | The original device type code |
| `reason` | `missing_color_field` or `invalid_color_value` or `number_code_mismatch` |
| `color_value` / `actual_number_code` | The problematic field value |
| `csv_row` | Full CSV row for debugging |

All successful replacements appear in the `CODE REPLACEMENTS (DEVICE TYPE CODES UPDATED)` report.


# `pt convert` — Unit / timestamp / number-base converter

Three independent verbs bundled under one group: physical units, timestamps, and number bases.

> No extra needed — uses base deps + `pint` + `python-dateutil`.

## Verbs

| Verb | Purpose |
|---|---|
| [`unit`](#pt-convert-unit) | Convert physical units (km↔mi, kg↔lb, °C↔°F, ...) |
| [`timestamp`](#pt-convert-timestamp) | Convert between epoch seconds/ms and ISO 8601 / RFC 822 |
| [`base`](#pt-convert-base) | Convert numbers between bases (bin/oct/dec/hex) |

---

## `pt convert unit`

Convert quantities between any units `pint` supports.

### Synopsis

```
pt convert unit "VALUE [SPACE] UNIT" -t|--to TARGET
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `VALUE` | str | yes | Quantity with unit, e.g. `"100 km"` or `"3 hours"`. Quote the whole thing if it contains a space. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--to` | `-t` | str | **required** | Target unit, e.g. `mi`. |

### Examples

```bash
pt convert unit "100 km" --to mi             # → 62.1371 mi
pt convert unit "20 degC" --to degF          # → 68.0000 °F
pt convert unit "5 hours" --to seconds       # → 18000.0000 s
pt convert unit "1 kg" --to lb               # → 2.2046 lb
pt convert unit "1 cubic_meter" --to liter   # → 1000.0000 L
pt convert unit "100 mph" --to "km/hour"     # → 160.9344 km/h
```

### Notes

- Output is formatted as `{:.4f~P}` (4 decimal places, pretty unit).
- Offset units like Celsius/Fahrenheit work because `autoconvert_offset_to_baseunit` is enabled.
- `pint` ships a huge unit registry — see [pint's defaults](https://pint.readthedocs.io/en/stable/getting/defining-quantities.html).

### Errors

- `Could not convert '<value>' to '<target>': <reason>` — bad input or incompatible units.

---

## `pt convert timestamp`

Convert between Unix epoch (seconds or milliseconds) and ISO 8601 / RFC 822.

### Synopsis

```
pt convert timestamp VALUE [-t|--to iso|epoch|epoch-ms|rfc822]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `VALUE` | str | yes | Either an integer (epoch seconds, or milliseconds if `> 10^12`) or an ISO/RFC date string. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--to` | `-t` | enum | `iso` | Target form: `iso`, `epoch`, `epoch-ms`, `rfc822`. |

### Auto-detection

- Input that's all digits with `abs > 10^12` is interpreted as **milliseconds**.
- Otherwise, all-digit input is interpreted as **seconds**.
- Anything else is parsed by `dateutil` (handles ISO 8601, RFC 2822, and many human-readable variants). UTC is assumed when no timezone is supplied.

### Examples

```bash
pt convert timestamp 1715200000                          # → 2024-05-08T20:26:40+00:00
pt convert timestamp 1715200000000 --to iso              # ms input
pt convert timestamp "2025-04-08T20:26:40Z" --to epoch
pt convert timestamp "2025-04-08T20:26:40Z" --to rfc822  # → Tue, 08 Apr 2025 20:26:40 +0000
pt convert timestamp now --to epoch                      # → current epoch (dateutil parses "now")
```

### Errors

- `Could not parse '<value>'` — neither numeric nor parseable date.
- `Unknown target '<x>'` — pick `iso`, `epoch`, `epoch-ms`, `rfc822`.

---

## `pt convert base`

Convert integers between binary, octal, decimal, and hex.

### Synopsis

```
pt convert base VALUE [-t|--to BASE] [-f|--from BASE]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `VALUE` | str | yes | The number. May include `0x`, `0b`, or `0o` prefix to encode the source base. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--to` | `-t` | enum | `10` | Target base: `2`/`bin`, `8`/`oct`, `10`/`dec`, `16`/`hex`. |
| `--from` | `-f` | enum | auto | Source base. Required when input has no prefix and isn't decimal. |

### Examples

```bash
pt convert base 0xff --to 10                # → 255
pt convert base 255 --to hex                # → ff
pt convert base 11111111 --from 2 --to dec  # → 255
pt convert base 0b1010 --to 16              # → a
pt convert base -42 --to bin                # → -101010
```

### Notes

- Output never has a `0x` / `0b` / `0o` prefix — easy to copy into code or assembly.
- Negative numbers are supported and emit a leading `-`.

### Errors

- `Could not parse '<value>'` — pass `--from` or use a `0x`/`0b`/`0o` prefix.
- `'<value>' is not a base-<n> number` — input contains digits invalid for the source base.
- `Unknown source/target base '<x>'` — typo.

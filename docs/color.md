# `pt color` — Color converter

Convert colors between hex, rgb, hsl, hsv, and cmyk.

> No extra needed — uses stdlib `colorsys`.

## Verbs

| Verb | Purpose |
|---|---|
| [`convert`](#pt-color-convert) | Convert a color to one or all formats |

---

## `pt color convert`

### Synopsis

```
pt color convert SPEC [-t|--to FORMAT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SPEC` | str | yes | Color in any supported input form (see below). |

### Accepted input forms

| Form | Example |
|---|---|
| Hex `#RRGGBB` | `#3366ff` |
| Hex `#RGB` (short) | `#f00` (= `#ff0000`) |
| RGB | `rgb(51,102,255)` or `rgba(51,102,255,0.8)` |
| HSL | `hsl(220,100%,60%)` or `hsla(220,100%,60%,0.8)` |
| HSV | `hsv(220,80%,100%)` |

(Whitespace is flexible.)

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--to` | `-t` | enum | `all` | Target format: `hex`, `rgb`, `hsl`, `hsv`, `cmyk`, or `all` (prints all five). |

### Examples

```bash
pt color convert "#3366ff"                   # prints all 5 forms
pt color convert "rgb(51,102,255)" --to hsl  # → hsl(220, 100%, 60%)
pt color convert "hsl(220,100%,60%)" --to hex
pt color convert "#f00" --to cmyk            # → cmyk(0%, 100%, 100%, 0%)
pt color convert "#3366ff" --to rgb          # → rgb(51, 102, 255)
```

### Output forms

- **hex** → `#3366ff` (lowercase, 6 digits)
- **rgb** → `rgb(R, G, B)` (0-255)
- **hsl** → `hsl(H, S%, L%)` (0-360 / 0-100 / 0-100, integer)
- **hsv** → `hsv(H, S%, V%)`
- **cmyk** → `cmyk(C%, M%, Y%, K%)` (integer)

### Errors

- `Could not parse '<spec>'` — input didn't match any supported form.
- `Unknown target '<x>'` — typo in `--to`.

### Notes

- All conversions go through normalized 0..1 RGB internally. Round-tripping through HSL/HSV may shift by ±1 due to integer rounding in the output format.
- Alpha channels in `rgba(...)` / `hsla(...)` are ignored — output is always opaque.

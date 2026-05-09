# `pt qr` — QR codes

Generate QR codes (PNG/SVG/PDF/EPS/terminal), Wi-Fi join codes, decode QRs from images.

> Generation needs no extra (segno is a base dep). Decoding requires `[qr-decode]` (pyzbar — and `libzbar` system package on Linux).

## Verbs

| Verb | Purpose | Extra |
|---|---|---|
| [`gen`](#pt-qr-gen) | Generate a QR code | (none — base) |
| [`wifi`](#pt-qr-wifi) | Generate a Wi-Fi join QR | (none — base) |
| [`decode`](#pt-qr-decode) | Decode a QR from an image | `[qr-decode]` + `[img]` |

---

## `pt qr gen`

Generate a QR code from text. Output format is picked by the file extension.

### Synopsis

```
pt qr gen TEXT [-o|--output OUTPUT] [--scale N] [--border N]
               [-e|--error l|m|q|h] [--terminal/--no-terminal]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `TEXT` | str | yes | Content to encode. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | `qr.png` | Output file. Allowed extensions: `.png`, `.svg`, `.pdf`, `.eps`, `.txt`. |
| `--scale` | — | int | `8` | Pixel scale factor (PNG/SVG). Larger = bigger image. |
| `--border` | — | int | `4` | Quiet zone width in modules. |
| `--error` | `-e` | enum | `m` | Error correction level: `l` ~7%, `m` ~15%, `q` ~25%, `h` ~30%. Higher = bigger code but more damage-tolerant. |
| `--terminal` / `--no-terminal` | — | flag | `--no-terminal` | Print compact ASCII to the terminal instead of writing a file. |

### Examples

```bash
# Default PNG
pt qr gen "https://github.com/k6w/polytool"

# Save as SVG (vector, infinite zoom)
pt qr gen "Hello!" -o qr.svg

# Print to terminal (no file)
pt qr gen "secret" --terminal

# High-error-correction QR (good for sticker prints that may get scratched)
pt qr gen "https://example.com" -e h --scale 12 -o sticker.png
```

### Errors

- `Could not encode text: <reason>` — usually the input was too long for the chosen error level.
- `Unsupported output extension '.xyz'` — only `.png`, `.svg`, `.pdf`, `.eps`, `.txt` are allowed.

---

## `pt qr wifi`

Generate a Wi-Fi join QR code. When scanned by a phone, the user is prompted to join the network with no typing.

### Synopsis

```
pt qr wifi SSID [-p|--password PASSWORD] [--auth WPA|WPA2|WEP|""]
                [--hidden] [-o|--output OUTPUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SSID` | str | yes | Network name. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--password` | `-p` | str | `""` | Password (omit / empty for open networks). |
| `--auth` | — | enum | `WPA2` | `WPA`, `WPA2`, `WEP`, or `""` for open networks. |
| `--hidden` | — | flag | off | Network has a hidden SSID. |
| `--output` | `-o` | path | `wifi.png` | Output PNG. |

### Examples

```bash
pt qr wifi MyHomeWiFi --password hunter2
pt qr wifi Office --password "S@feCorp" --auth WPA2 -o office-wifi.png
pt qr wifi Guest --password "" --auth ""    # open network
```

---

## `pt qr decode`

Decode QR codes from an image and print the contents.

### Synopsis

```
pt qr decode IMAGE
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `IMAGE` | path | yes | Image file containing one or more QR codes. |

### Examples

```bash
pt qr decode qr.png
pt qr decode photo-of-qr.jpg
pt qr decode screenshot.png    # multiple QRs → one decoded line each
```

### Errors

- `No QR code found in <path>` — image too low contrast / occluded / not a QR.
- `Missing optional dependency: 'pyzbar'` — install `[qr-decode]`. On Linux you also need `libzbar0`: `sudo apt-get install libzbar0`.

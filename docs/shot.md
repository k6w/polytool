# `pt shot` — Screenshots

Capture the screen (any monitor) and full-page web screenshots.

> `screen` requires the `[shot]` extra (mss). `web` requires `[shot]` plus a one-time Chromium install via `pt shot install` (Playwright).

## Verbs

| Verb | Purpose |
|---|---|
| [`screen`](#pt-shot-screen) | Capture the screen (any monitor or all) |
| [`web`](#pt-shot-web) | Take a full-page or viewport screenshot of a URL |
| [`install`](#pt-shot-install) | One-time: download Chromium for `web` |

---

## `pt shot screen`

Save a screen capture to PNG. Powered by [`mss`](https://github.com/BoboTiG/python-mss) — fast and no system deps on Windows or macOS.

### Synopsis

```
pt shot screen [-o|--output OUTPUT] [-m|--monitor INDEX]
```

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | `screen.png` | Output PNG. |
| `--monitor` | `-m` | int | `0` | `0` = all monitors stitched, `1` = primary, `2` = second, ... |

### Examples

```bash
pt shot screen
pt shot screen -o ~/Desktop/snap.png
pt shot screen --monitor 2 -o second-monitor.png
```

### Errors

- `Monitor index <N> out of range (0..M)` — pick a valid monitor.
- On headless Linux, capture will fail without `DISPLAY` or `WAYLAND_DISPLAY`.

---

## `pt shot web`

Render a URL with Chromium (Playwright) and screenshot it.

### Synopsis

```
pt shot web URL [-o|--output OUTPUT] [--full-page|--viewport]
                [--width PX] [--height PX] [--wait MS]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `URL` | str | yes | URL to capture. |

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--output`, `-o` | path | `page.png` | Output PNG. |
| `--full-page` / `--viewport` | flag | `--full-page` | Capture entire scroll height vs. just the viewport. |
| `--width` | int | `1280` | Viewport width (px). |
| `--height` | int | `800` | Viewport height (px). |
| `--wait` | int (ms) | `0` | Extra time to wait after page load (for animations / lazy content). |

### Examples

```bash
pt shot web https://example.com
pt shot web https://example.com --viewport --width 1920 --height 1080
pt shot web https://news.example.com --full-page --wait 2000
```

### Notes

- Page is loaded with `wait_until="networkidle"`, so most pages settle before the screenshot.
- `--full-page` captures the entire scrollable height. Use `--viewport` for a fixed-size shot.
- Chromium is installed once via `pt shot install`; subsequent runs reuse it.

### Errors

- `Playwright Chromium not installed.` — run `pt shot install`.
- Other Playwright errors are surfaced verbatim with a hint to run `pt shot install`.

---

## `pt shot install`

Run `python -m playwright install chromium` to fetch the browser. ~150 MB download, one-time.

### Synopsis

```
pt shot install
```

### Examples

```bash
pt shot install
```

### Errors

- `Playwright not found.` — install the `[shot]` extra first: `uv tool install 'polytool[shot]'`.
- `playwright install failed (exit N)` — Playwright's installer failed; check the printed output above.

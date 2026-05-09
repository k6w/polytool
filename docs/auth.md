# Auth & external services — full audit

Most of polytool runs locally and never touches the network. This page lists every verb that does, and exactly what auth options exist for each.

## Verbs that touch the network

| Verb | External service | Auth supported | Persistable? |
|---|---|---|---|
| [`pt dl get`](dl.md#pt-dl-get) | yt-dlp / 1700+ sites | cookies (from-browser or cookies.txt), `--username`/`--password`, `--video-password` | ✅ via `pt dl setup` |
| [`pt dl info`](dl.md#pt-dl-info) | yt-dlp / 1700+ sites | same as `dl get` | ✅ via `pt dl setup` |
| [`pt net ip-info`](net.md#pt-net-ip-info) | `ip-api.com` (free tier) | none — keyless free tier | n/a |
| [`pt net http`](net.md#pt-net-http) | any URL the user gives | user supplies via `-H "Authorization: ..."`, `--data`, `--json` | n/a |
| [`pt net port-check`](net.md#pt-net-port-check) | raw TCP — no protocol auth | n/a | n/a |
| [`pt shot web`](shot.md#pt-shot-web) | Playwright Chromium → public web | **none yet** — see below | ❌ planned |

## Verbs that do NOT touch the network

These are 100% local; nothing to authenticate to:

- All of `pt img` (incl. `bg-remove`, `ocr`, `palette`, `watermark`, `ascii`, `exif`)
- All of `pt vid` (uses local `ffmpeg`)
- All of `pt pdf` (incl. `ocr`)
- All of `pt data`, `pt enc`, `pt qr` (gen + decode), `pt gen`, `pt file`, `pt clip`, `pt color`, `pt convert`, `pt text`, `pt cron`
- `pt shot screen` (local screen capture via `mss`)

## Persistent setup commands

Run these once and forget — saved at `~/.polytool/config.toml` (or `%USERPROFILE%\.polytool\config.toml` on Windows).

### `pt dl setup`

```bash
# Interactive — picks chrome/firefox/edge/brave/chromium/opera/safari/vivaldi/whale
pt dl setup

# Non-interactive
pt dl setup --browser firefox                 # any saved browser
pt dl setup --browser chrome:Default          # specific profile
pt dl setup --cookies ~/cookies.txt           # cookies.txt path

# Inspect / clear
pt dl setup --show
pt dl setup --clear
```

### Bot-check auto-hint

When `pt dl get/info` hits a "sign in / not a bot / captcha / private / members-only" error, polytool prints a green hint pointing at `pt dl setup` so you don't have to remember the command name.

## Per-call auth flags (no setup, no persistence)

For one-off use or scripts that intentionally vary credentials per invocation, every auth-bearing verb accepts inline flags. These always **override** the saved config for that call.

### `pt dl get/info`

| Flag | Effect |
|---|---|
| `--cookies-from-browser SPEC` | Use a browser's cookies for just this call. |
| `--cookies cookies.txt` | Use a Netscape-format file for just this call. |
| `-u/--username USER` | Form-login username. |
| `-p/--password PWD` | Form-login password. Omit and yt-dlp will prompt securely. |
| `--video-password PWD` | Per-video password (Vimeo etc.). |

### `pt net http`

Pass the auth header directly:

```bash
pt net http GET https://api.example.com -H "Authorization: Bearer $TOKEN"
pt net http POST https://api.example.com -H "X-API-Key: $KEY" --json '{}'
```

## Auth scenarios that polytool does NOT yet handle

Filed for future versions:

- **`pt shot web` to logged-in pages.** Right now Playwright launches a clean Chromium, so private dashboards / paywalled pages render as the unauthenticated view. Adding `pt shot setup --browser chrome` (with cookie extraction) is planned.
- **`pt net ip-info` with an API key for higher rate limits.** ip-api.com's free tier is fine for casual use; if you need a paid token, open an issue.
- **2FA prompts** for `pt dl get/info` username/password. Most sites with 2FA expect cookies anyway — use `pt dl setup --browser <yours>` after solving 2FA in the browser.

## Where credentials live

- **`pt dl setup`** writes a single TOML file at `~/.polytool/config.toml` containing the chosen browser identifier (e.g. `firefox`) or a path to your cookies file. **No passwords or cookies are stored** — only a *pointer* to where yt-dlp should read them.
- **`--username`/`--password`/`--video-password`** are only kept in process memory for the duration of a single command. They are not written to disk by polytool. (yt-dlp may cache its own download state, but not your credentials.)
- **Cookies themselves** stay where they were: in your browser's cookie database, or in the `cookies.txt` file you point to.

## Removing credentials

```bash
pt dl setup --clear         # forget the saved browser/cookies pointer
```

To remove cookies from the browser itself, use the browser's settings.

To shred a `cookies.txt` file, use `pt file dedupe` to find duplicates first, then delete with your OS tool of choice (`rm` / `Remove-Item`).

## Privacy

polytool sends no telemetry. The only outbound network calls happen when you explicitly ask for them: `pt dl`, `pt shot web`, `pt net *`, and (on first use) the one-time downloads of:

- ffmpeg (~70 MB) on first `pt vid …` if no system ffmpeg
- U2-Net model (~170 MB) on first `pt img bg-remove`
- Chromium (~150 MB) when you opt in via `pt shot install`

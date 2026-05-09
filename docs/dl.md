# `pt dl` — Download from YouTube and 1000+ sites

A thin, well-behaved wrapper around [yt-dlp](https://github.com/yt-dlp/yt-dlp). Persistent cookie config (`pt dl setup`) so you don't have to pass auth flags every time. Audio-only mode, format selection, custom templates, username/password and per-video-password all pass straight through to yt-dlp.

> Requires the `[dl]` extra.

## Verbs

| Verb | Purpose |
|---|---|
| [`setup`](#pt-dl-setup) | One-time: tell `pt dl` where to fetch cookies from |
| [`get`](#pt-dl-get) | Download a media URL |
| [`info`](#pt-dl-info) | Print metadata about a URL without downloading |

## How auth works (read this first)

Many sites — YouTube especially — return a "sign in to confirm you're not a bot" challenge to anonymous downloaders. yt-dlp solves this by using your **browser's cookies**.

You have three options, in order of convenience:

1. **One-time setup, used forever (recommended):**
   ```bash
   pt dl setup --browser firefox      # or chrome / edge / brave / ...
   ```
   After this, every `pt dl get` and `pt dl info` automatically loads cookies from that browser. No flags needed per call.

2. **Per-call override:** pass `--cookies-from-browser BROWSER` or `--cookies cookies.txt`.
3. **Username / password:** for sites with login forms, pass `--username` / `--password` (or `--video-password` for per-video passwords like Vimeo's). One-off — these are not persisted.

Polytool detects bot-check error patterns and points you at `pt dl setup` automatically.

---

## `pt dl setup`

Save a default cookie source so subsequent downloads work without flags.

### Synopsis

```
pt dl setup                              # interactive prompt
pt dl setup -b|--browser BROWSER         # save a default browser
pt dl setup --cookies COOKIES.TXT        # save a Netscape cookies file
pt dl setup --show                       # show current saved config
pt dl setup --clear                      # forget saved cookies
```

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--browser` | `-b` | str | — | Save a browser as the default. Same `BROWSER[+keyring][:profile][::container]` format yt-dlp uses. |
| `--cookies` | — | path | — | Save a Netscape-format cookies.txt path. Mutually exclusive with `--browser`. |
| `--show` | — | flag | off | Print the saved config (and the file location). |
| `--clear` | — | flag | off | Remove the saved cookie config. |

If no flags are passed, `pt dl setup` runs interactively and prompts you to pick a browser.

### Supported browsers

**Native** (handled by yt-dlp directly):
chrome · firefox · edge · brave · chromium · opera · safari · vivaldi · whale

**Firefox forks** (polytool resolves the profile path itself, then hands it to yt-dlp's firefox extractor):
**zen** · **librewolf** · **waterfox** · **floorp** · **mullvad**

For Firefox forks polytool reads the fork's standard `profiles.ini` to find the default profile (or the named profile if you pass `:profile-name`). Cross-platform — works on Linux, macOS, and Windows.

> **Don't see your browser?** If it's a Chromium-based fork (Arc, Yandex, Sidekick, etc.), yt-dlp can't auto-extract its cookies. Workaround: export the cookies manually with a browser extension like [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) and use `pt dl setup --cookies cookies.txt`.

The config lives at `~/.polytool/config.toml` (POSIX) or `%USERPROFILE%\.polytool\config.toml` (Windows).

### Examples

```bash
pt dl setup                                  # interactive
pt dl setup --browser firefox                # save firefox as default
pt dl setup --browser chrome:Default         # save chrome's "Default" profile
pt dl setup --browser firefox+gnomekeyring   # firefox using gnomekeyring
pt dl setup --browser zen                    # Zen Browser (Firefox fork)
pt dl setup --browser zen:work               # Zen with the "work" profile
pt dl setup --browser librewolf              # LibreWolf
pt dl setup --browser waterfox               # Waterfox
pt dl setup --browser floorp                 # Floorp
pt dl setup --browser mullvad                # Mullvad Browser
pt dl setup --cookies ~/cookies.txt          # save a cookies file
pt dl setup --show
pt dl setup --clear
```

### Picking a browser that's actually logged in

The browser you pick must have an active session for the target site. So if you're trying to download YouTube videos, log into YouTube in that browser at least once first.

---

## `pt dl get`

Download a media URL.

### Synopsis

```
pt dl get URL [-o|--output DIR] [-a|--audio-only] [-f|--format SELECTOR]
              [-t|--template TEMPLATE]
              [--cookies-from-browser SPEC | --cookies FILE]
              [-u|--username USER] [-p|--password PWD] [--video-password PWD]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `URL` | str | yes | Any of [yt-dlp's 1700+ sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md). |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | `.` | Output directory. Created if missing. |
| `--audio-only` | `-a` | flag | off | Download audio only and convert to MP3 (192k via ffmpeg postprocessor). Implies `bestaudio/best`. |
| `--format` | `-f` | str | yt-dlp default | yt-dlp format selector — e.g. `best`, `bestvideo+bestaudio`, `720p`, `mp4`. Ignored with `--audio-only`. |
| `--template` | `-t` | str | `%(title)s.%(ext)s` | yt-dlp output filename template. |
| `--cookies-from-browser` | — | str | from `dl setup` | Per-call override of saved browser config. |
| `--cookies` | — | path | from `dl setup` | Per-call override with a Netscape cookies file. |
| `--username` | `-u` | str | — | Account username (for sites with form-based login auth). |
| `--password` | `-p` | str | — | Account password. Tip: omit and yt-dlp will securely prompt. |
| `--video-password` | — | str | — | Per-video password (e.g. Vimeo private videos with their own password). |

### Examples

```bash
# Default — uses cookies from `pt dl setup`
pt dl get 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

# Audio-only as MP3
pt dl get URL --audio-only

# 720p, into a specific folder
pt dl get URL --format 720p -o ./downloads/

# Custom filename template
pt dl get URL -t "%(uploader)s - %(title)s.%(ext)s"

# Whole playlist (yt-dlp default behavior; nothing extra needed)
pt dl get 'https://www.youtube.com/playlist?list=...'

# Per-call cookie override (skips saved config for this call)
pt dl get URL --cookies-from-browser chrome

# Username + password (for sites that need them)
pt dl get URL --username alice --password 'hunter2'

# Per-video password (Vimeo / private hosting)
pt dl get URL --video-password 'secret'
```

### Errors

| Message | Most likely cause | Fix |
|---|---|---|
| `Missing optional dependency: 'yt_dlp'` | `[dl]` extra not installed | `uv tool install 'polytool[dl]'` |
| `Download failed: Sign in to confirm you're not a bot` | YouTube bot challenge | `pt dl setup --browser <your-browser>` |
| `Download failed: HTTP Error 429` | Rate-limited | wait, or use a different account |
| `Download failed: Members-only / Premium content` | account not entitled | log into the account that owns it, then `pt dl setup` |
| `Download failed: Private video` | needs login | log in via your browser, then `pt dl setup` |
| `Download failed: requires --video-password` | per-video password (Vimeo) | re-run with `--video-password` |

---

## `pt dl info`

Print useful metadata about a URL without downloading.

### Synopsis

```
pt dl info URL
            [--cookies-from-browser SPEC | --cookies FILE]
            [-u|--username USER] [-p|--password PWD] [--video-password PWD]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `URL` | str | yes | Media URL. |

### Options

Same auth-related options as `pt dl get` (see above).

### Examples

```bash
pt dl info 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
pt dl info URL --cookies-from-browser chrome    # one-off override
pt dl info URL --username alice --password hunter2
```

### Output fields

When available, these are printed (cyan key, white value):

- `title`
- `uploader`
- `duration` (seconds)
- `view_count`
- `upload_date` (YYYYMMDD)
- `webpage_url`

---

## What about `pt shot web` and other commands that touch the network?

See [auth.md](auth.md) for the full audit of which polytool verbs touch external services and whether they need auth.

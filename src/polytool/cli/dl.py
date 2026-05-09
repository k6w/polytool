"""Download media from YouTube and 1000+ sites via yt-dlp."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from polytool.core import config
from polytool.core.browsers import (
    ALL_BROWSERS,
    FIREFOX_FORK_DIRS,
    YT_DLP_NATIVE_BROWSERS,
    find_firefox_fork_data_dir,
    resolve_firefox_profile_dir,
)
from polytool.core.console import console, err_console
from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="dl",
    help="Download media from YouTube and 1000+ sites (yt-dlp).",
    no_args_is_help=True,
)

# Browsers `pt dl setup` accepts. Includes yt-dlp's native list plus the
# Firefox forks we resolve ourselves (zen, librewolf, waterfox, floorp, mullvad).
SUPPORTED_BROWSERS = ALL_BROWSERS

BOT_CHECK_HINTS = (
    "sign in",
    "confirm you",
    "not a bot",
    "captcha",
    "private video",
    "members-only",
    "login required",
    "rate limit",
)


def _parse_browser_spec(spec: str) -> tuple[str, str | None, str | None, str | None]:
    """Parse a polytool browser spec and return a yt-dlp-ready tuple.

    Format: ``browser[+keyring][:profile][::container]``.

    For yt-dlp's native browsers this is a pass-through. For Firefox forks
    (zen / librewolf / waterfox / floorp / mullvad), we locate the user's
    data dir + profile directory and return ``('firefox', <abs-path>, …)`` —
    yt-dlp's firefox extractor accepts an absolute profile path.

    >>> _parse_browser_spec("chrome")
    ('chrome', None, None, None)
    >>> _parse_browser_spec("firefox:default-release")
    ('firefox', 'default-release', None, None)
    >>> _parse_browser_spec("firefox+gnomekeyring:default::personal")
    ('firefox', 'default', 'gnomekeyring', 'personal')
    """
    rest = spec
    container: str | None = None
    if "::" in rest:
        rest, _, container = rest.partition("::")
    profile: str | None = None
    if ":" in rest:
        rest, _, profile = rest.partition(":")
    keyring: str | None = None
    if "+" in rest:
        rest, _, keyring = rest.partition("+")
    browser = rest.strip().lower()
    if not browser:
        raise PolytoolError(
            f"Invalid --cookies-from-browser spec: {spec!r}",
            hint="Format: browser[+keyring][:profile][::container].",
        )

    # Firefox forks: resolve profile dir ourselves, pass it to yt-dlp as firefox.
    if browser in FIREFOX_FORK_DIRS:
        data_dir = find_firefox_fork_data_dir(browser)
        if data_dir is None:
            raise PolytoolError(
                f"Could not find {browser!r} data directory.",
                hint=(
                    f"Make sure {browser} is installed and has been launched at "
                    f"least once on this machine."
                ),
            )
        try:
            profile_dir = resolve_firefox_profile_dir(data_dir, profile)
        except FileNotFoundError as exc:
            raise PolytoolError(str(exc)) from exc
        return ("firefox", str(profile_dir), keyring or None, container or None)

    if browser not in YT_DLP_NATIVE_BROWSERS:
        raise PolytoolError(
            f"Unknown browser {browser!r}.",
            hint=f"Supported: {', '.join(SUPPORTED_BROWSERS)}.",
        )
    return (browser, profile or None, keyring or None, container or None)


def _resolve_cookies(
    cookies_from_browser: str | None,
    cookies_file: Path | None,
) -> tuple[str | None, Path | None]:
    """Pick the active cookie source: explicit flags first, then saved config."""
    if cookies_from_browser and cookies_file:
        raise PolytoolError("Use --cookies-from-browser OR --cookies, not both.")
    if cookies_from_browser:
        return cookies_from_browser, None
    if cookies_file:
        return None, cookies_file
    saved_browser = config.get("dl", "cookies_from_browser")
    saved_file = config.get("dl", "cookies_file")
    if saved_browser:
        return saved_browser, None
    if saved_file:
        return None, Path(saved_file)
    return None, None


def _apply_cookie_opts(
    opts: dict,
    cookies_from_browser: str | None,
    cookies_file: Path | None,
) -> None:
    """Mutate *opts* in-place to add yt-dlp cookie options."""
    browser_spec, file_path = _resolve_cookies(cookies_from_browser, cookies_file)
    if browser_spec:
        opts["cookiesfrombrowser"] = _parse_browser_spec(browser_spec)
    elif file_path:
        if not file_path.exists():
            raise PolytoolError(f"Cookie file not found: {file_path}")
        opts["cookiefile"] = str(file_path)


def _bot_check_hint(message: str) -> str | None:
    low = message.lower()
    if not any(s in low for s in BOT_CHECK_HINTS):
        return None
    if config.get("dl", "cookies_from_browser") or config.get("dl", "cookies_file"):
        return (
            "Saved cookies didn't satisfy the site. "
            "Re-run [cyan]pt dl setup[/cyan] (maybe pick a different browser/profile)."
        )
    return (
        "This site is blocking unauthenticated requests. "
        "Run [cyan]pt dl setup[/cyan] once to configure cookies, "
        "or pass [cyan]--cookies-from-browser BROWSER[/cyan] per call."
    )


@app.command("setup")
def cmd_setup(
    browser: Annotated[
        str | None,
        typer.Option(
            "--browser",
            "-b",
            help=f"Save a default browser ({', '.join(SUPPORTED_BROWSERS)}). "
            "Accepts the same browser[+keyring][:profile][::container] format as yt-dlp.",
        ),
    ] = None,
    cookies_file: Annotated[
        Path | None,
        typer.Option("--cookies", help="Save the path to a Netscape-format cookies.txt file."),
    ] = None,
    clear: Annotated[bool, typer.Option("--clear", help="Remove the saved cookie config.")] = False,
    show: Annotated[bool, typer.Option("--show", help="Print the saved cookie config.")] = False,
) -> None:
    """One-time setup: tell `pt dl` where to fetch cookies from.

    After running this, [cyan]pt dl get[/cyan] and [cyan]pt dl info[/cyan] will
    automatically use your saved cookies — no need to pass flags every time.

    Examples:

        pt dl setup                       # interactive prompt
        pt dl setup --browser firefox     # save firefox as the default
        pt dl setup --browser chrome:Default
        pt dl setup --cookies cookies.txt
        pt dl setup --show                # print current saved config
        pt dl setup --clear               # forget saved cookies
    """
    from polytool.core.config import CONFIG_PATH

    if show:
        b = config.get("dl", "cookies_from_browser")
        f = config.get("dl", "cookies_file")
        if not b and not f:
            console.print("[dim]No saved dl cookie config.[/dim]")
            return
        if b:
            console.print(f"[cyan]cookies-from-browser[/cyan]: {b}")
        if f:
            console.print(f"[cyan]cookies-file[/cyan]: {f}")
        console.print(f"[dim](stored at {CONFIG_PATH})[/dim]")
        return

    if clear:
        config.unset("dl", "cookies_from_browser")
        config.unset("dl", "cookies_file")
        console.print("[green]Cleared saved dl cookie config.[/green]")
        return

    if browser is not None and cookies_file is not None:
        raise PolytoolError("Use --browser OR --cookies, not both.")

    if browser is None and cookies_file is None:
        # Interactive prompt.
        console.print("Which browser should [cyan]pt dl[/cyan] pull cookies from?\n")
        for i, name in enumerate(SUPPORTED_BROWSERS, 1):
            console.print(f"  [cyan]{i}[/cyan]) {name}")
        console.print(f"  [cyan]{len(SUPPORTED_BROWSERS) + 1}[/cyan]) [dim]none / not now[/dim]")
        choice_s = typer.prompt("\nPick a number", type=str)
        try:
            choice = int(choice_s.strip())
        except ValueError as exc:
            raise PolytoolError(f"Not a number: {choice_s!r}") from exc
        if choice == len(SUPPORTED_BROWSERS) + 1:
            console.print("[dim]Skipped. Run pt dl setup any time to configure.[/dim]")
            return
        if not 1 <= choice <= len(SUPPORTED_BROWSERS):
            raise PolytoolError("Out of range.")
        browser = SUPPORTED_BROWSERS[choice - 1]

    if browser is not None:
        # Validate the spec parses (catches typos before the user hits a real error later).
        _parse_browser_spec(browser)
        config.set_(browser, "dl", "cookies_from_browser")
        config.unset("dl", "cookies_file")
        console.print(
            f"[green]Saved.[/green] [cyan]pt dl[/cyan] will use cookies from "
            f"[bold]{browser}[/bold] from now on."
        )
        console.print(f"[dim](config at {CONFIG_PATH})[/dim]")
        return

    assert cookies_file is not None
    if not cookies_file.exists():
        raise PolytoolError(f"Cookie file not found: {cookies_file}")
    resolved = cookies_file.resolve()
    config.set_(str(resolved), "dl", "cookies_file")
    config.unset("dl", "cookies_from_browser")
    console.print(f"[green]Saved.[/green] [cyan]pt dl[/cyan] will use cookies from {resolved}.")
    console.print(f"[dim](config at {CONFIG_PATH})[/dim]")


@app.command("get")
def cmd_get(
    url: Annotated[str, typer.Argument(help="Media URL")],
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path(),
    audio_only: Annotated[
        bool,
        typer.Option("--audio-only", "-a", help="Download audio (mp3) only"),
    ] = False,
    format_: Annotated[
        str | None,
        typer.Option("--format", "-f", help="yt-dlp format selector (e.g. 'best', '720p')"),
    ] = None,
    template: Annotated[
        str,
        typer.Option(
            "--template",
            "-t",
            help="Output filename template (yt-dlp syntax)",
        ),
    ] = "%(title)s.%(ext)s",
    cookies_from_browser: Annotated[
        str | None,
        typer.Option(
            "--cookies-from-browser",
            help="Override saved config: load cookies from BROWSER[+keyring][:profile][::container].",
        ),
    ] = None,
    cookies_file: Annotated[
        Path | None,
        typer.Option(
            "--cookies",
            help="Override saved config: path to a Netscape-format cookies.txt file.",
        ),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option("--username", "-u", help="Account username (for sites with login auth)."),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password",
            "-p",
            help="Account password. Tip: omit and yt-dlp will prompt securely.",
        ),
    ] = None,
    video_password: Annotated[
        str | None,
        typer.Option("--video-password", help="Per-video password (Vimeo etc.)."),
    ] = None,
) -> None:
    """Download a video or audio file.

    Cookies are taken from your [cyan]pt dl setup[/cyan] config by default;
    override per-call with --cookies-from-browser / --cookies.

    Examples:

        pt dl get 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        pt dl get URL --audio-only
        pt dl get URL --format 720p -o ./downloads/
        pt dl get URL --cookies-from-browser firefox     # one-off override
        pt dl get URL --username alice --password 'hunter2'
        pt dl get URL --video-password 'secret'          # Vimeo-style per-video pwd
    """
    from polytool.core.lazy import require_extra

    yt_dlp = require_extra("yt_dlp", extra="dl")

    output_dir.mkdir(parents=True, exist_ok=True)
    opts: dict = {
        "outtmpl": str(output_dir / template),
        "noplaylist": False,
        "quiet": False,
        "no_warnings": False,
        "progress": True,
    }
    if audio_only:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]
    elif format_:
        opts["format"] = format_

    _apply_cookie_opts(opts, cookies_from_browser, cookies_file)
    if username is not None:
        opts["username"] = username
    if password is not None:
        opts["password"] = password
    if video_password is not None:
        opts["videopassword"] = video_password
    if "cookiesfrombrowser" in opts and not (cookies_from_browser or cookies_file):
        err_console.print(
            f"[dim]Using saved cookies-from-browser: {opts['cookiesfrombrowser'][0]}[/dim]"
        )

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        raise PolytoolError(f"Download failed: {exc}", hint=_bot_check_hint(str(exc))) from exc
    except Exception as exc:
        raise PolytoolError(f"Download failed: {exc}", hint=_bot_check_hint(str(exc))) from exc
    console.print("[green]Done.[/green]")


@app.command("info")
def cmd_info(
    url: Annotated[str, typer.Argument(help="Media URL")],
    cookies_from_browser: Annotated[
        str | None,
        typer.Option(
            "--cookies-from-browser",
            help="Override saved config: load cookies from BROWSER[+keyring][:profile][::container].",
        ),
    ] = None,
    cookies_file: Annotated[
        Path | None,
        typer.Option(
            "--cookies",
            help="Override saved config: path to a Netscape-format cookies.txt file.",
        ),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option("--username", "-u", help="Account username (for sites with login auth)."),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password",
            "-p",
            help="Account password. Tip: omit and yt-dlp will prompt securely.",
        ),
    ] = None,
    video_password: Annotated[
        str | None,
        typer.Option("--video-password", help="Per-video password (Vimeo etc.)."),
    ] = None,
) -> None:
    """Show metadata about a URL without downloading.

    Cookies are taken from your [cyan]pt dl setup[/cyan] config by default.

    Examples:

        pt dl info 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        pt dl info URL --cookies-from-browser chrome
        pt dl info URL --username alice --password hunter2
    """
    from polytool.core.lazy import require_extra

    yt_dlp = require_extra("yt_dlp", extra="dl")

    opts: dict = {"quiet": True, "no_warnings": True}
    _apply_cookie_opts(opts, cookies_from_browser, cookies_file)
    if username is not None:
        opts["username"] = username
    if password is not None:
        opts["password"] = password
    if video_password is not None:
        opts["videopassword"] = video_password
    if "cookiesfrombrowser" in opts and not (cookies_from_browser or cookies_file):
        err_console.print(
            f"[dim]Using saved cookies-from-browser: {opts['cookiesfrombrowser'][0]}[/dim]"
        )

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        raise PolytoolError(f"Could not fetch info: {exc}", hint=_bot_check_hint(str(exc))) from exc

    interesting = ("title", "uploader", "duration", "view_count", "upload_date", "webpage_url")
    for key in interesting:
        if key in info and info[key] is not None:
            console.print(f"[cyan]{key}[/cyan]: {info[key]}")

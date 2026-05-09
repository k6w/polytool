"""Download media from YouTube and 1000+ sites via yt-dlp."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import typer
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from polytool.core import config, runtime
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

# Patterns that indicate YouTube's n-challenge / JS-runtime gap.
N_CHALLENGE_PATTERNS = (
    "n challenge",
    "only images are available",
    "requested format is not available",
)

# Patterns that indicate per-session DRM lock — not something we can solve.
DRM_PATTERNS = (
    "drm protected",
    "drm-protected",
    "experiment that applies drm",
)


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# Lines we *never* show — pure status output from yt-dlp's discovery pipeline.
_PROGRESS_NOISE_RE = re.compile(
    r"^(?:Extracting URL|Downloading\s\S+|Extracting cookies|Extracted\s|"
    r"\[\w+\]\s|Sleeping|Skipping|Deleting original file)"
)

# Per-client warnings yt-dlp emits while it tries multiple YouTube extractors.
# These are informational — when at least one client succeeds, the user
# doesn't need to know that the others were skipped. We capture them in the
# logger so the n-challenge hint can still see them if the download ultimately
# fails, but we don't print them to the terminal during a successful run.
_CLIENT_NOISE_PATTERNS = (
    "n challenge solving failed",
    "some formats may be missing",
    "client https formats require a gvs po token",
    "client hls formats require a gvs po token",
    "client formats require a gvs po token",
    "have been skipped as they are drm protected",
    "experiment that applies drm",
    "skipped as they are drm",
    "ensure you have a supported javascript runtime",
)


def _strip(msg: object) -> str:
    text = _ANSI_RE.sub("", str(msg)).strip()
    for prefix in ("WARNING:", "ERROR:", "[generic]", "[youtube]"):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
    return text


def _is_noise(text: str) -> bool:
    if _PROGRESS_NOISE_RE.match(text):
        return True
    low = text.lower()
    return any(p in low for p in _CLIENT_NOISE_PATTERNS)


class _DlLogger:
    """Capture yt-dlp warnings/errors. Filter the noisy per-client status
    warnings out of terminal output (still recorded for hint generation).
    """

    def __init__(self, verbose: bool = False) -> None:
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.verbose = verbose

    def debug(self, msg: object) -> None:
        pass

    def info(self, msg: object) -> None:
        pass

    def warning(self, msg: object) -> None:
        clean = _strip(msg)
        if not clean:
            return
        self.warnings.append(clean)
        if self.verbose or not _is_noise(clean):
            err_console.print(f"[yellow]warning:[/yellow] {clean}")

    def error(self, msg: object) -> None:
        clean = _strip(msg)
        if clean:
            self.errors.append(clean)


def _make_progress() -> Progress:
    """Rich progress bar tuned for downloads (title · bar · % · size · speed · ETA)."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>5.1f}%"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=err_console,
        transient=False,
    )


def _make_progress_hook(progress: Progress, state: dict):
    """Build a yt-dlp progress hook that drives the Rich progress bar.

    Also stashes the final filename/size/title in *state* so the success
    summary can read them after the download completes.
    """

    def hook(d: dict) -> None:
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            info = d.get("info_dict") or {}
            title = info.get("title") or Path(d.get("filename", "download")).name
            disp = title if len(title) <= 50 else title[:47] + "..."
            state["title"] = title
            tid = state.get("task_id")
            if tid is None:
                state["task_id"] = progress.add_task(disp, total=total)
            else:
                progress.update(tid, completed=downloaded, total=total, description=disp)
        elif status == "finished":
            info = d.get("info_dict") or {}
            state["filename"] = d.get("filename") or info.get("_filename") or ""
            state["total_bytes"] = d.get("total_bytes") or d.get("total_bytes_estimate")
            tid = state.pop("task_id", None)
            if tid is not None and progress.tasks[tid].total:
                progress.update(tid, completed=progress.tasks[tid].total)

    return hook


def _human_size(n: int | None) -> str:
    if not n:
        return "—"
    f = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if f < 1024:
            return f"{f:.1f} {unit}"
        f /= 1024
    return f"{f:.1f} PB"


def _human_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"


def _n_challenge_hint(messages: list[str]) -> str | None:
    text = " ".join(messages).lower()
    if not any(p in text for p in N_CHALLENGE_PATTERNS):
        return None

    # When cookies are configured we know we're in a logged-in session — that's
    # by far the most common cause of these errors (YouTube tightens access for
    # accounts in their DRM A/B bucket). Try anonymous access first.
    using_cookies = bool(
        config.get("dl", "cookies_from_browser") or config.get("dl", "cookies_file")
    )

    fixes: list[str] = []
    if using_cookies:
        fixes.append(
            "[bold]Most likely fix:[/bold] try without cookies. YouTube often gates "
            "logged-in sessions into a DRM-only bucket.\n"
            "  [cyan]pt dl setup --clear[/cyan]    [dim]# forget saved cookies (just for testing)[/dim]\n"
            "  [cyan]pt dl get URL[/cyan]\n"
            "If that works, re-save cookies for sites that need them: "
            "[cyan]pt dl setup --browser firefox[/cyan]"
        )
    fixes.append(
        "If it still fails, make sure a JS runtime is on PATH. Polytool can manage one:\n"
        "  [cyan]pt dl runtime install[/cyan]    "
        "[dim]# downloads Deno (~50 MB) into ~/.polytool/runtime/[/dim]"
    )
    fixes.append(
        "Some videos are flagged DRM in your specific YouTube session — those can't "
        "be downloaded by any tool. Try a different video or account."
    )

    return "\n\n".join(fixes)


def _drm_hint(messages: list[str]) -> str | None:
    text = " ".join(messages).lower()
    if not any(p in text for p in DRM_PATTERNS):
        return None
    return (
        "YouTube has flagged this video as DRM-protected for your current session.\n"
        "This is a per-account / per-session A/B experiment yt-dlp can't bypass.\n\n"
        "Workarounds (any one usually works):\n"
        "  • Try without cookies: [cyan]pt dl get URL --cookies-from-browser ''[/cyan]\n"
        "  • Use a different browser profile: [cyan]pt dl setup --browser chrome[/cyan]\n"
        "  • Try a different YouTube account.\n"
        "  • Pick a different video — only some are DRM-flagged in your session."
    )


def _hint_for_error(message: str, logger: _DlLogger) -> str | None:
    """Pick the best hint for a failure: DRM > bot-check > n-challenge."""
    pool = [message, *logger.warnings, *logger.errors]
    return _drm_hint(pool) or _bot_check_hint(message) or _n_challenge_hint(pool)


# --------------------------------------------------------------------------- #
# `pt dl runtime` — manage the bundled JS runtime
# --------------------------------------------------------------------------- #
runtime_app = typer.Typer(
    name="runtime",
    help="Manage the bundled JavaScript runtime (Deno) used to solve YouTube's n-challenge.",
    no_args_is_help=True,
)


@runtime_app.command("install")
def cmd_runtime_install(
    force: Annotated[
        bool, typer.Option("--force", help="Re-download even if already installed.")
    ] = False,
) -> None:
    """Download Deno into ~/.polytool/runtime/ for yt-dlp to use.

    Examples:

        pt dl runtime install
        pt dl runtime install --force
    """
    sys_path = runtime.system_runtime_path()
    if sys_path and not force:
        console.print(
            f"[green]A system JS runtime is already on PATH:[/green] {sys_path}\n"
            "[dim]No managed Deno needed. Pass --force to install anyway.[/dim]"
        )
        return
    if runtime.is_managed_deno_installed() and not force:
        console.print(
            f"[green]Managed Deno already installed:[/green] {runtime.deno_binary_path()}\n"
            "[dim]Pass --force to re-download.[/dim]"
        )
        return
    try:
        binary = runtime.install_deno()
    except Exception as exc:
        raise PolytoolError(f"Could not install Deno: {exc}") from exc
    runtime.ensure_runtime_in_path()
    console.print(f"[green]Installed Deno[/green] at [bold]{binary}[/bold]")


@runtime_app.command("show")
def cmd_runtime_show() -> None:
    """Show the current JS-runtime status (system or managed).

    Examples:

        pt dl runtime show
    """
    sys_path = runtime.system_runtime_path()
    if sys_path:
        console.print(f"[cyan]system runtime:[/cyan] {sys_path}")
    if runtime.is_managed_deno_installed():
        console.print(f"[cyan]managed deno:[/cyan]  {runtime.deno_binary_path()}")
    if not sys_path and not runtime.is_managed_deno_installed():
        console.print("[dim]No JS runtime found.[/dim]")
        console.print("Run [cyan]pt dl runtime install[/cyan] to fetch one.")


@runtime_app.command("clear")
def cmd_runtime_clear() -> None:
    """Remove the managed Deno install at ~/.polytool/runtime/.

    Examples:

        pt dl runtime clear
    """
    if not runtime.RUNTIME_DIR.exists():
        console.print("[dim]Nothing to clear — managed runtime dir doesn't exist.[/dim]")
        return
    runtime.remove_runtime()
    console.print(f"[green]Removed[/green] {runtime.RUNTIME_DIR}")


app.add_typer(runtime_app, name="runtime")


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
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show every yt-dlp warning (not just the user-actionable ones).",
        ),
    ] = False,
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
        pt dl get URL --verbose                          # show all warnings
    """
    import time

    from polytool.core.lazy import require_extra

    yt_dlp = require_extra("yt_dlp", extra="dl")

    output_dir.mkdir(parents=True, exist_ok=True)
    # Make sure a JS runtime is reachable before we hit yt-dlp. If nothing is
    # installed, fetch Deno automatically (one-time ~50 MB) — this is what the
    # user expects from `polytool[full]`: it just works.
    if runtime.ensure_runtime_in_path() is None:
        err_console.print("[dim]no JS runtime found — fetching Deno (~50 MB, one-time)...[/dim]")
        try:
            runtime.install_deno()
            runtime.ensure_runtime_in_path()
        except Exception as exc:
            err_console.print(
                f"[yellow]warning:[/yellow] auto-install failed: {exc}\n"
                "[dim]Run [cyan]pt dl runtime install[/cyan] manually, "
                "or install Deno/Node yourself.[/dim]"
            )
    logger = _DlLogger(verbose=verbose)
    progress = _make_progress()
    state: dict = {}
    opts: dict = {
        "outtmpl": str(output_dir / template),
        "noplaylist": False,
        "quiet": True,  # silence yt-dlp's stdout — we render our own UI
        "no_warnings": True,  # warnings flow through our logger instead
        "noprogress": True,  # we render a Rich progress bar
        "logger": logger,
        "progress_hooks": [_make_progress_hook(progress, state)],
        # Try multiple YouTube clients — `tv` alone often fails the n-challenge
        # while web/android/ios still return usable formats. yt-dlp aggregates
        # formats across all clients before selecting.
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "web_safari", "mweb", "android", "ios", "tv"],
            }
        },
    }
    if audio_only:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]
    elif format_:
        opts["format"] = format_
    else:
        # `bv*+ba/b/18` — best video+audio, else best single, else fallback
        # to YouTube's reliable 360p mp4 (format 18) which never needs the
        # n-challenge solver and is available almost universally.
        opts["format"] = "bv*+ba/b/18"

    _apply_cookie_opts(opts, cookies_from_browser, cookies_file)
    if username is not None:
        opts["username"] = username
    if password is not None:
        opts["password"] = password
    if video_password is not None:
        opts["videopassword"] = video_password
    if "cookiesfrombrowser" in opts and not (cookies_from_browser or cookies_file):
        err_console.print(f"[dim]cookies: {opts['cookiesfrombrowser'][0]}[/dim]")

    started = time.monotonic()
    try:
        with progress, yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        raise PolytoolError(
            f"Download failed: {_strip(exc)}", hint=_hint_for_error(str(exc), logger)
        ) from exc
    except Exception as exc:
        raise PolytoolError(
            f"Download failed: {_strip(exc)}", hint=_hint_for_error(str(exc), logger)
        ) from exc

    elapsed = time.monotonic() - started
    title = state.get("title") or "download"
    filename = state.get("filename")
    size = state.get("total_bytes")
    out_path = Path(filename) if filename else None

    console.print()
    console.print(f"  [green bold]done[/green bold]  [bold]{title}[/bold]")
    if out_path is not None:
        try:
            display_path = out_path.resolve().relative_to(Path.cwd())
        except (ValueError, OSError):
            display_path = out_path
        console.print(
            f"        [dim]{display_path}  "
            f"({_human_size(size)} in {_human_duration(elapsed)})[/dim]"
        )
    else:
        console.print(f"        [dim]({_human_size(size)} in {_human_duration(elapsed)})[/dim]")


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

    runtime.ensure_runtime_in_path()
    logger = _DlLogger()
    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "logger": logger,
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "web_safari", "mweb", "android", "ios", "tv"],
            }
        },
    }
    _apply_cookie_opts(opts, cookies_from_browser, cookies_file)
    if username is not None:
        opts["username"] = username
    if password is not None:
        opts["password"] = password
    if video_password is not None:
        opts["videopassword"] = video_password
    if "cookiesfrombrowser" in opts and not (cookies_from_browser or cookies_file):
        err_console.print(f"[dim]cookies: {opts['cookiesfrombrowser'][0]}[/dim]")

    # process=False skips yt-dlp's format-selection step. We only want metadata,
    # and on some sites (YouTube especially) the default format selector
    # fails with "Requested format is not available" on otherwise-valid videos.
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False, process=False)
    except Exception as exc:
        raise PolytoolError(
            f"Could not fetch info: {_strip(exc)}", hint=_hint_for_error(str(exc), logger)
        ) from exc

    if info is None:
        raise PolytoolError("yt-dlp returned no metadata for this URL.")

    interesting = (
        "title",
        "uploader",
        "channel",
        "duration",
        "view_count",
        "like_count",
        "upload_date",
        "live_status",
        "webpage_url",
    )
    shown = False
    for key in interesting:
        if key in info and info[key] is not None:
            console.print(f"[cyan]{key}[/cyan]: {info[key]}")
            shown = True
    # Playlists and some sites return only `entries` and a few top-level fields.
    if not shown and info.get("_type") == "playlist":
        console.print(f"[cyan]playlist[/cyan]: {info.get('title') or info.get('id')}")
        entries = info.get("entries") or []
        console.print(f"[cyan]entries[/cyan]: {len(list(entries))}")

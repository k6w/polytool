"""Download media from YouTube and 1000+ sites via yt-dlp."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from polytool.core.console import console
from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="dl",
    help="Download media from YouTube and 1000+ sites (yt-dlp).",
    no_args_is_help=True,
)


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
) -> None:
    """Download a video or audio file.

    Examples:

        pt dl get 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        pt dl get URL --audio-only
        pt dl get URL --format 720p -o ./downloads/
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

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        raise PolytoolError(f"Download failed: {exc}") from exc
    except Exception as exc:
        raise PolytoolError(f"Download failed: {exc}") from exc
    console.print("[green]Done.[/green]")


@app.command("info")
def cmd_info(
    url: Annotated[str, typer.Argument(help="Media URL")],
) -> None:
    """Show metadata about a URL without downloading.

    Examples:

        pt dl info 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    """
    from polytool.core.lazy import require_extra

    yt_dlp = require_extra("yt_dlp", extra="dl")

    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        raise PolytoolError(f"Could not fetch info: {exc}") from exc

    interesting = ("title", "uploader", "duration", "view_count", "upload_date", "webpage_url")
    for key in interesting:
        if key in info and info[key] is not None:
            console.print(f"[cyan]{key}[/cyan]: {info[key]}")

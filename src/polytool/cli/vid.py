"""Video / audio utilities — convert, trim, extract-audio, gif (all via ffmpeg)."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from polytool.core.console import console
from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="vid",
    help="Video/audio utilities (convert, trim, extract-audio, gif).",
    no_args_is_help=True,
)


def _run_ffmpeg(args: list[str]) -> None:
    from polytool.core.ffmpeg import ffmpeg_path

    cmd = [ffmpeg_path(), "-y", "-hide_banner", "-loglevel", "error", *args]
    console.print(f"[dim]$ ffmpeg {' '.join(shlex.quote(a) for a in args)}[/dim]")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise PolytoolError(f"ffmpeg failed (exit {exc.returncode})") from exc


@app.command("convert")
def cmd_convert(
    source: Annotated[Path, typer.Argument(help="Input video/audio")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output file")],
    crf: Annotated[
        int | None,
        typer.Option("--crf", help="Quality 0-51 (lower=better; default: codec preset)"),
    ] = None,
) -> None:
    """Convert between video/audio formats (mp4, mkv, webm, mp3, wav, ogg, ...).

    Examples:

        pt vid convert clip.mov -o clip.mp4
        pt vid convert song.wav -o song.mp3
        pt vid convert clip.mp4 -o clip.webm --crf 30
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    args = ["-i", str(source)]
    if crf is not None:
        args += ["-crf", str(crf)]
    args += [str(output)]
    _run_ffmpeg(args)
    console.print(f"[green]Wrote[/green] {output}")


@app.command("trim")
def cmd_trim(
    source: Annotated[Path, typer.Argument(help="Input file")],
    start: Annotated[str, typer.Option("--start", "-s", help="Start (HH:MM:SS or seconds)")] = "0",
    end: Annotated[
        str | None, typer.Option("--end", "-e", help="End (HH:MM:SS or seconds)")
    ] = None,
    duration: Annotated[
        str | None, typer.Option("--duration", "-d", help="Length (HH:MM:SS or seconds)")
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output (default: <name>_trim.<ext>)"),
    ] = None,
) -> None:
    """Trim a video or audio file. Use --end OR --duration.

    Examples:

        pt vid trim clip.mp4 --start 0:10 --end 0:30
        pt vid trim clip.mp4 -s 5 -d 10
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    if end and duration:
        raise PolytoolError("Use --end OR --duration, not both.")
    out = output or source.with_stem(source.stem + "_trim")
    args = ["-ss", start, "-i", str(source)]
    if end is not None:
        args += ["-to", end]
    if duration is not None:
        args += ["-t", duration]
    args += ["-c", "copy", str(out)]
    _run_ffmpeg(args)
    console.print(f"[green]Wrote[/green] {out}")


@app.command("extract-audio")
def cmd_extract_audio(
    source: Annotated[Path, typer.Argument(help="Input video")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output (default: <name>.mp3)"),
    ] = None,
    bitrate: Annotated[str, typer.Option("--bitrate", help="e.g. 192k")] = "192k",
) -> None:
    """Extract the audio track from a video as MP3 (or other format by extension).

    Examples:

        pt vid extract-audio movie.mp4
        pt vid extract-audio movie.mp4 -o sound.wav
        pt vid extract-audio movie.mp4 --bitrate 320k
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    out = output or source.with_suffix(".mp3")
    args = ["-i", str(source), "-vn"]
    if out.suffix.lower() == ".wav":
        args += ["-c:a", "pcm_s16le"]
    else:
        args += ["-b:a", bitrate]
    args += [str(out)]
    _run_ffmpeg(args)
    console.print(f"[green]Wrote[/green] {out}")


@app.command("gif")
def cmd_gif(
    source: Annotated[Path, typer.Argument(help="Input video")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output (default: <name>.gif)"),
    ] = None,
    fps: Annotated[int, typer.Option("--fps", help="Frames per second")] = 12,
    width: Annotated[int, typer.Option("--width", "-w", help="Output width (px)")] = 480,
    start: Annotated[str | None, typer.Option("--start", "-s", help="Start time")] = None,
    duration: Annotated[str | None, typer.Option("--duration", "-d", help="Length")] = None,
) -> None:
    """Convert a video clip to an animated GIF.

    Examples:

        pt vid gif clip.mp4
        pt vid gif clip.mp4 --fps 24 --width 720
        pt vid gif clip.mp4 -s 0:10 -d 5
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    out = output or source.with_suffix(".gif")
    args: list[str] = []
    if start is not None:
        args += ["-ss", start]
    args += ["-i", str(source)]
    if duration is not None:
        args += ["-t", duration]
    vf = f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
    args += ["-vf", vf, "-loop", "0", str(out)]
    _run_ffmpeg(args)
    console.print(f"[green]Wrote[/green] {out}")

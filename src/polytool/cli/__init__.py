"""Root Typer app — subcommand groups are added by their own modules.

Subcommand modules must keep top-level imports light (typer/rich/stdlib only).
Heavy imports (Pillow, ffmpeg, rembg) happen inside command bodies via
`polytool.core.lazy.require_extra`.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Annotated

import typer

from polytool import __version__
from polytool.cli import (
    clip,
    color,
    convert,
    cron,
    data,
    dl,
    enc,
    file,
    gen,
    img,
    net,
    pdf,
    qr,
    shot,
    text,
    vid,
)
from polytool.core import runtime
from polytool.core.console import console, err_console
from polytool.core.errors import PolytoolError, render_panel

app = typer.Typer(
    name="polytool",
    help="polytool — one-binary CLI bundling 26 everyday utilities (pt for short).",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
    # We handle PolytoolError ourselves via the `main()` wrapper below; disable
    # Typer's pretty-traceback so it doesn't squash our hints.
    pretty_exceptions_enable=False,
)


def _force_utf8_io() -> None:
    """On Windows the default code page is often cp1252 and unicode chars
    in Rich output trip ``UnicodeEncodeError``. Reconfigure stdout/stderr to
    UTF-8 with a safe fallback before any Rich output happens.
    """
    import contextlib

    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, OSError):
            stream.reconfigure(encoding="utf-8", errors="replace")


def run() -> None:
    """Console-script entry point — runs the Typer app and renders PolytoolError nicely.

    (Defined with a unique name to avoid clashing with the ``@app.callback()``
    function below — both would otherwise be named ``main`` in this module.)
    """
    _force_utf8_io()
    try:
        app()
    except PolytoolError as exc:
        render_panel(exc.message, exc.hint)
        sys.exit(1)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"polytool {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """polytool — one-binary CLI bundling 26 everyday utilities."""


@app.command("setup")
def cmd_setup(
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip prompts; install everything."),
    ] = False,
    skip_runtime: Annotated[
        bool,
        typer.Option("--skip-runtime", help="Don't fetch Deno (used by `pt dl get`)."),
    ] = False,
    skip_chromium: Annotated[
        bool,
        typer.Option(
            "--skip-chromium", help="Don't fetch Playwright Chromium (used by `pt shot web`)."
        ),
    ] = False,
) -> None:
    """One-shot post-install: fetch every binary the [full] extra needs.

    Most polytool features work the moment you `uv tool install 'polytool[full]'`.
    A handful need extra one-time downloads that aren't pip packages:

    - **Deno (~50 MB)** — solves YouTube's n-challenge for `pt dl get`.
    - **Playwright Chromium (~150 MB)** — used by `pt shot web`.

    `pt setup` fetches both. Run it once and you're done; you can also run
    each install separately via `pt dl runtime install` and `pt shot install`.

    Examples:

        pt setup                # interactive; default-yes to each step
        pt setup -y             # silent; install everything
        pt setup --skip-chromium  # everything except Chromium
    """
    steps: list[tuple[str, str, callable]] = []  # type: ignore[type-arg]

    if not skip_runtime:
        steps.append(
            (
                "JS runtime (Deno)",
                "for `pt dl get` to solve YouTube's n-challenge",
                _install_runtime_step,
            )
        )
    if not skip_chromium:
        steps.append(
            (
                "Playwright Chromium",
                "for `pt shot web`",
                _install_chromium_step,
            )
        )

    if not steps:
        console.print("[dim]Nothing to do — both --skip-* flags set.[/dim]")
        return

    console.print("[bold]polytool setup[/bold]\n")
    console.print("This will fetch one-time downloads needed by certain commands:\n")
    for name, why, _ in steps:
        console.print(f"  • [cyan]{name}[/cyan] — {why}")
    console.print()

    if not yes and not typer.confirm("Continue?", default=True):
        console.print("[dim]Cancelled.[/dim]")
        return

    failures: list[str] = []
    for name, _why, step in steps:
        console.print(f"[bold]→ {name}[/bold]")
        try:
            step()
        except Exception as exc:
            failures.append(f"{name}: {exc}")
            err_console.print(f"[red]failed:[/red] {exc}")
        console.print()

    if failures:
        msg = "Some steps failed:\n  " + "\n  ".join(failures)
        raise PolytoolError(msg)
    console.print("[green]All set.[/green] You can now use every polytool command.")


def _install_runtime_step() -> None:
    sys_runtime = runtime.system_runtime_path()
    if sys_runtime:
        console.print(f"[green]system runtime already on PATH:[/green] {sys_runtime}")
        return
    if runtime.is_managed_deno_installed():
        console.print(f"[green]already installed:[/green] {runtime.deno_binary_path()}")
        return
    binary = runtime.install_deno()
    runtime.ensure_runtime_in_path()
    console.print(f"[green]installed:[/green] {binary}")


def _install_chromium_step() -> None:
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Playwright Python package missing. Install with: uv tool install 'polytool[shot]'"
        ) from exc
    console.print("[green]Chromium installed.[/green]")


app.add_typer(enc.app, name="enc")
app.add_typer(gen.app, name="gen")
app.add_typer(color.app, name="color")
app.add_typer(convert.app, name="convert")
app.add_typer(text.app, name="text")
app.add_typer(data.app, name="data")
app.add_typer(qr.app, name="qr")
app.add_typer(clip.app, name="clip")
app.add_typer(cron.app, name="cron")
app.add_typer(net.app, name="net")
app.add_typer(file.app, name="file")
app.add_typer(img.app, name="img")
app.add_typer(pdf.app, name="pdf")
app.add_typer(vid.app, name="vid")
app.add_typer(dl.app, name="dl")
app.add_typer(shot.app, name="shot")


__all__ = ["app"]

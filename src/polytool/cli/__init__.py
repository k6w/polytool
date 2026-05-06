"""Root Typer app — subcommand groups are added by their own modules.

Subcommand modules must keep top-level imports light (typer/rich/stdlib only).
Heavy imports (Pillow, ffmpeg, rembg) happen inside command bodies via
`polytool.core.lazy.require_extra`.
"""

from __future__ import annotations

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
from polytool.core.errors import install_excepthook

install_excepthook()

app = typer.Typer(
    name="polytool",
    help="polytool — one-binary CLI bundling 26 everyday utilities (pt for short).",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)


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

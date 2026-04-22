"""QR code generation (segno) and decoding (pyzbar)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from polytool.core.errors import PolytoolError
from polytool.core.io import default_output

app = typer.Typer(
    name="qr",
    help="QR code generate and decode.",
    no_args_is_help=True,
)


@app.command("gen")
def cmd_gen(
    text: Annotated[str, typer.Argument(help="Content to encode")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file (.png, .svg, .pdf, .eps); default: qr.png"),
    ] = None,
    scale: Annotated[
        int, typer.Option("--scale", help="Pixel scale (PNG/SVG)")
    ] = 8,
    border: Annotated[int, typer.Option("--border", help="Quiet zone in modules")] = 4,
    error: Annotated[
        str, typer.Option("--error", "-e", help="Error correction: l, m, q, h")
    ] = "m",
    terminal: Annotated[
        bool,
        typer.Option("--terminal/--no-terminal", help="Print ASCII to terminal"),
    ] = False,
) -> None:
    """Generate a QR code.

    Examples:

        pt qr gen "https://github.com/k6w/polytool"
        pt qr gen "wifi:S=Home;P=secret;T=WPA2;;" --output wifi.png
        pt qr gen "text" --terminal
        pt qr gen "text" --output qr.svg --scale 10
    """
    import segno

    try:
        qr = segno.make(text, error=error)
    except Exception as exc:
        raise PolytoolError(f"Could not encode text: {exc}") from exc

    if terminal:
        qr.terminal(compact=True)
        return

    out = output or Path("qr.png")
    suffix = out.suffix.lower()
    if suffix not in {".png", ".svg", ".pdf", ".eps", ".txt"}:
        raise PolytoolError(
            f"Unsupported output extension {suffix!r}",
            hint="Use .png, .svg, .pdf, .eps, or .txt",
        )
    qr.save(str(out), scale=scale, border=border)
    typer.echo(f"Wrote {out}")


@app.command("decode")
def cmd_decode(
    image: Annotated[Path, typer.Argument(help="Image file containing a QR code.")],
) -> None:
    """Decode a QR code from an image.

    Examples:

        pt qr decode qr.png
        pt qr decode photo-of-qr.jpg
    """
    if not image.exists():
        raise PolytoolError(f"File not found: {image}")
    from polytool.core.lazy import require_extra

    pyzbar = require_extra("pyzbar.pyzbar", extra="qr-decode")
    PIL_Image = require_extra("PIL.Image", extra="img")  # noqa: N806

    img = PIL_Image.open(image)
    results = pyzbar.decode(img)
    if not results:
        raise PolytoolError(
            f"No QR code found in {image}",
            hint="Make sure the image is high-contrast and the code is unobstructed.",
        )
    for r in results:
        typer.echo(r.data.decode("utf-8", errors="replace"))


@app.command("wifi")
def cmd_wifi(
    ssid: Annotated[str, typer.Argument(help="Network SSID")],
    password: Annotated[
        str, typer.Option("--password", "-p", help="Network password")
    ] = "",
    auth: Annotated[
        str, typer.Option("--auth", help="WPA, WPA2, WEP, or '' for open")
    ] = "WPA2",
    hidden: Annotated[bool, typer.Option("--hidden", help="Hidden SSID")] = False,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Output file (default: wifi.png)")
    ] = None,
) -> None:
    """Generate a Wi-Fi join QR code (scan with phone).

    Examples:

        pt qr wifi MyNetwork --password hunter2
        pt qr wifi Guest --password "" --auth ""
    """
    import segno
    from segno import helpers

    qr = helpers.make_wifi(ssid=ssid, password=password or None, security=auth or None, hidden=hidden)
    out = output or Path("wifi.png")
    qr.save(str(out), scale=8, border=4)
    typer.echo(f"Wrote {out}")
    _ = segno  # keep linter aware import is intended

"""Color converter (hex / rgb / hsl / hsv / cmyk)."""

from __future__ import annotations

import colorsys
import re
from typing import Annotated

import typer

from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="color",
    help="Convert colors between hex, rgb, hsl, hsv, cmyk.",
    no_args_is_help=True,
)

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
RGB_RE = re.compile(r"^rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)")
HSL_RE = re.compile(
    r"^hsla?\s*\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*%\s*,\s*(\d+(?:\.\d+)?)\s*%"
)
HSV_RE = re.compile(
    r"^hsva?\s*\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*%\s*,\s*(\d+(?:\.\d+)?)\s*%"
)


def _parse(spec: str) -> tuple[float, float, float]:
    """Parse any supported color spec into normalized 0..1 RGB."""
    s = spec.strip()
    m = HEX_RE.match(s)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r = int(h[0:2], 16) / 255
        g = int(h[2:4], 16) / 255
        b = int(h[4:6], 16) / 255
        return r, g, b
    m = RGB_RE.match(s)
    if m:
        return int(m.group(1)) / 255, int(m.group(2)) / 255, int(m.group(3)) / 255
    m = HSL_RE.match(s)
    if m:
        h = float(m.group(1)) / 360
        l_ = float(m.group(3)) / 100
        sat = float(m.group(2)) / 100
        r, g, b = colorsys.hls_to_rgb(h, l_, sat)
        return r, g, b
    m = HSV_RE.match(s)
    if m:
        h = float(m.group(1)) / 360
        sat = float(m.group(2)) / 100
        v = float(m.group(3)) / 100
        r, g, b = colorsys.hsv_to_rgb(h, sat, v)
        return r, g, b
    raise PolytoolError(
        f"Could not parse color {spec!r}",
        hint="Try forms like #3366ff, rgb(51,102,255), hsl(220,100%,60%).",
    )


def _to_hex(r: float, g: float, b: float) -> str:
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def _to_rgb(r: float, g: float, b: float) -> str:
    return f"rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})"


def _to_hsl(r: float, g: float, b: float) -> str:
    h, l_, s = colorsys.rgb_to_hls(r, g, b)
    return f"hsl({h * 360:.0f}, {s * 100:.0f}%, {l_ * 100:.0f}%)"


def _to_hsv(r: float, g: float, b: float) -> str:
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return f"hsv({h * 360:.0f}, {s * 100:.0f}%, {v * 100:.0f}%)"


def _to_cmyk(r: float, g: float, b: float) -> str:
    k = 1 - max(r, g, b)
    if k >= 1:
        return "cmyk(0%, 0%, 0%, 100%)"
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return f"cmyk({c * 100:.0f}%, {m * 100:.0f}%, {y * 100:.0f}%, {k * 100:.0f}%)"


@app.command("convert")
def cmd_convert(
    spec: Annotated[
        str, typer.Argument(help="Color in hex, rgb(...), hsl(...), or hsv(...).")
    ],
    to: Annotated[
        str, typer.Option("--to", "-t", help="hex | rgb | hsl | hsv | cmyk | all")
    ] = "all",
) -> None:
    """Convert a color between formats.

    Examples:

        pt color convert "#3366ff"
        pt color convert "rgb(51,102,255)" --to hsl
        pt color convert "hsl(220,100%,60%)" --to cmyk
    """
    r, g, b = _parse(spec)
    converters = {
        "hex": _to_hex,
        "rgb": _to_rgb,
        "hsl": _to_hsl,
        "hsv": _to_hsv,
        "cmyk": _to_cmyk,
    }
    if to == "all":
        for name, fn in converters.items():
            typer.echo(f"{name:5} {fn(r, g, b)}")
    else:
        fn = converters.get(to.lower())
        if fn is None:
            raise PolytoolError(
                f"Unknown target {to!r}",
                hint=f"One of: {', '.join(converters)}",
            )
        typer.echo(fn(r, g, b))

"""Unit / timestamp / number-base converter."""

from __future__ import annotations

from typing import Annotated

import typer

from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="convert",
    help="Unit, timestamp, number-base converters.",
    no_args_is_help=True,
)


@app.command("unit")
def cmd_unit(
    value: Annotated[
        str, typer.Argument(help="Value with unit, e.g. '100 km' or '3 hours'.")
    ],
    to: Annotated[str, typer.Option("--to", "-t", help="Target unit, e.g. 'mi'.")],
) -> None:
    """Convert physical units (length, mass, time, temperature, ...).

    Examples:

        pt convert unit "100 km" --to mi
        pt convert unit "20 degC" --to degF
        pt convert unit "5 hours" --to seconds
    """
    import pint

    ureg = pint.UnitRegistry()
    ureg.autoconvert_offset_to_baseunit = True
    try:
        q = ureg.Quantity(value)
        result = q.to(to)
    except Exception as exc:
        raise PolytoolError(
            f"Could not convert {value!r} to {to!r}: {exc}",
            hint="Try units like 'km', 'mi', 'kg', 'lb', 'celsius', 'fahrenheit'.",
        ) from exc
    typer.echo(f"{result:.4f~P}")


@app.command("timestamp")
def cmd_timestamp(
    value: Annotated[
        str, typer.Argument(help="Unix epoch (sec or ms) or ISO datetime.")
    ],
    to: Annotated[
        str, typer.Option("--to", "-t", help="Target: 'iso', 'epoch', 'epoch-ms', 'rfc822'")
    ] = "iso",
) -> None:
    """Convert between epoch seconds/ms and ISO 8601 / RFC 822.

    Examples:

        pt convert timestamp 1715200000
        pt convert timestamp 1715200000000 --to iso
        pt convert timestamp "2025-04-08T20:26:40Z" --to epoch
    """
    from datetime import UTC, datetime

    from dateutil import parser as dt_parser

    dt: datetime
    s = value.strip()
    if s.lstrip("-").isdigit():
        n = int(s)
        if abs(n) > 10**12:  # ms heuristic
            dt = datetime.fromtimestamp(n / 1000, tz=UTC)
        else:
            dt = datetime.fromtimestamp(n, tz=UTC)
    else:
        try:
            dt = dt_parser.parse(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
        except Exception as exc:
            raise PolytoolError(f"Could not parse {value!r}") from exc

    out = to.lower()
    if out == "iso":
        typer.echo(dt.isoformat())
    elif out == "epoch":
        typer.echo(str(int(dt.timestamp())))
    elif out == "epoch-ms":
        typer.echo(str(int(dt.timestamp() * 1000)))
    elif out == "rfc822":
        typer.echo(dt.strftime("%a, %d %b %Y %H:%M:%S %z"))
    else:
        raise PolytoolError(
            f"Unknown target {to!r}",
            hint="One of: iso, epoch, epoch-ms, rfc822",
        )


@app.command("base")
def cmd_base(
    value: Annotated[
        str,
        typer.Argument(help="Number in current base (use 0x/0b/0o prefix or --from)."),
    ],
    to: Annotated[
        str,
        typer.Option("--to", "-t", help="Target base: 2, 8, 10, 16 (or bin/oct/dec/hex)"),
    ] = "10",
    from_: Annotated[
        str | None,
        typer.Option("--from", "-f", help="Source base (default: auto-detect)"),
    ] = None,
) -> None:
    """Convert numbers between bases (binary, octal, decimal, hex).

    Examples:

        pt convert base 0xff --to 10
        pt convert base 255 --to hex
        pt convert base 11111111 --from 2 --to dec
    """
    bases = {"2": 2, "bin": 2, "8": 8, "oct": 8, "10": 10, "dec": 10, "16": 16, "hex": 16}
    target = bases.get(to.lower())
    if target is None:
        raise PolytoolError(f"Unknown target base {to!r}", hint="One of: 2/bin, 8/oct, 10/dec, 16/hex")

    if from_ is None:
        try:
            n = int(value, 0)
        except ValueError as exc:
            raise PolytoolError(
                f"Could not parse {value!r}",
                hint="Pass --from or use 0x/0b/0o prefix.",
            ) from exc
    else:
        src = bases.get(from_.lower())
        if src is None:
            raise PolytoolError(f"Unknown source base {from_!r}")
        try:
            n = int(value, src)
        except ValueError as exc:
            raise PolytoolError(f"{value!r} is not a base-{src} number") from exc

    if target == 2:
        typer.echo(bin(n)[2:] if n >= 0 else "-" + bin(-n)[2:])
    elif target == 8:
        typer.echo(oct(n)[2:] if n >= 0 else "-" + oct(-n)[2:])
    elif target == 10:
        typer.echo(str(n))
    elif target == 16:
        typer.echo(hex(n)[2:] if n >= 0 else "-" + hex(-n)[2:])

"""Data format converter (json / yaml / toml / csv / xml)."""

from __future__ import annotations

import csv as _csv
import io
import json as _json
import tomllib
from pathlib import Path
from typing import Annotated, Any

import typer

from polytool.core.errors import PolytoolError
from polytool.core.io import read_text, write_text

app = typer.Typer(
    name="data",
    help="Data format converter (json/yaml/toml/csv/xml).",
    no_args_is_help=True,
)

FORMATS = ("json", "yaml", "yml", "toml", "csv", "xml")


def _detect_format(path: Path | None, hint: str | None) -> str:
    if hint:
        h = hint.lower()
        if h not in FORMATS:
            raise PolytoolError(
                f"Unknown format {hint!r}",
                hint=f"One of: {', '.join(FORMATS)}",
            )
        return "yaml" if h == "yml" else h
    if path is None:
        raise PolytoolError(
            "Cannot detect format from stdin",
            hint="Pass --from json|yaml|toml|csv|xml.",
        )
    suffix = path.suffix.lstrip(".").lower()
    if suffix in {"yml"}:
        return "yaml"
    if suffix in FORMATS:
        return suffix
    raise PolytoolError(
        f"Cannot detect format from extension {suffix!r}",
        hint="Pass --from explicitly.",
    )


def _load(text: str, fmt: str) -> Any:
    if fmt == "json":
        return _json.loads(text)
    if fmt == "yaml":
        from ruamel.yaml import YAML

        return YAML(typ="safe").load(io.StringIO(text))
    if fmt == "toml":
        return tomllib.loads(text)
    if fmt == "csv":
        reader = _csv.DictReader(io.StringIO(text))
        return list(reader)
    if fmt == "xml":
        import xmltodict

        return xmltodict.parse(text)
    raise PolytoolError(f"Unsupported format: {fmt}")


def _dump(data: Any, fmt: str, *, pretty: bool = True) -> str:
    if fmt == "json":
        return _json.dumps(data, indent=2 if pretty else None, ensure_ascii=False) + "\n"
    if fmt == "yaml":
        from ruamel.yaml import YAML

        y = YAML()
        y.default_flow_style = False
        buf = io.StringIO()
        y.dump(data, buf)
        return buf.getvalue()
    if fmt == "toml":
        import tomli_w

        if not isinstance(data, dict):
            raise PolytoolError(
                "TOML output requires a top-level mapping",
                hint='Wrap your list in a key, e.g. {"items": [...]}.',
            )
        return tomli_w.dumps(data)
    if fmt == "csv":
        if not isinstance(data, list):
            raise PolytoolError(
                "CSV output requires a list of records",
                hint="Wrap your value in a JSON array of objects.",
            )
        if not data:
            return ""
        if not isinstance(data[0], dict):
            raise PolytoolError("CSV output requires a list of dicts")
        buf = io.StringIO(newline="")
        writer = _csv.DictWriter(buf, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
        return buf.getvalue()
    if fmt == "xml":
        import xmltodict

        if not isinstance(data, dict):
            raise PolytoolError(
                "XML output requires a top-level mapping",
                hint='Wrap data: {"root": {...}}',
            )
        return xmltodict.unparse(data, pretty=pretty)
    raise PolytoolError(f"Unsupported format: {fmt}")


@app.command("convert")
def cmd_convert(
    source: Annotated[
        Path | None, typer.Argument(help="Source file (or '-' / omit for stdin)")
    ] = None,
    to: Annotated[str, typer.Option("--to", "-t", help="Target: json|yaml|toml|csv|xml")] = "json",
    from_: Annotated[
        str | None,
        typer.Option("--from", "-f", help="Source format (default: from extension)"),
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Output file (default: stdout)")
    ] = None,
) -> None:
    """Convert between JSON / YAML / TOML / CSV / XML.

    Examples:

        pt data convert config.yaml --to json
        pt data convert data.csv --to json --output data.json
        cat x.toml | pt data convert --from toml --to yaml
    """
    src_fmt = _detect_format(source, from_)
    tgt_fmt = to.lower()
    if tgt_fmt == "yml":
        tgt_fmt = "yaml"
    if tgt_fmt not in FORMATS:
        raise PolytoolError(f"Unknown target {to!r}", hint=f"One of: {', '.join(FORMATS)}")
    text = read_text(source)
    data = _load(text, src_fmt)
    write_text(output, _dump(data, tgt_fmt))


@app.command("pretty")
def cmd_pretty(
    source: Annotated[Path | None, typer.Argument(help="File (or '-' / omit for stdin)")] = None,
    from_: Annotated[
        str | None, typer.Option("--from", "-f", help="Format (default: from extension)")
    ] = None,
) -> None:
    """Pretty-print structured data in its current format.

    Examples:

        pt data pretty messy.json
        cat x.yaml | pt data pretty --from yaml
    """
    fmt = _detect_format(source, from_)
    data = _load(read_text(source), fmt)
    typer.echo(_dump(data, fmt, pretty=True), nl=False)


@app.command("validate")
def cmd_validate(
    source: Annotated[Path | None, typer.Argument(help="File (or '-' / omit for stdin)")] = None,
    from_: Annotated[
        str | None, typer.Option("--from", "-f", help="Format (default: from extension)")
    ] = None,
) -> None:
    """Validate that a file parses cleanly. Exit 0 = valid, 1 = invalid.

    Examples:

        pt data validate config.yaml
        cat suspect.json | pt data validate --from json
    """
    fmt = _detect_format(source, from_)
    try:
        _load(read_text(source), fmt)
    except Exception as exc:
        raise PolytoolError(f"Invalid {fmt}: {exc}") from exc
    typer.echo(f"OK ({fmt})")

"""Text utilities (diff, wc, case-convert, slugify, markdown)."""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Annotated

import typer

from polytool.core.console import console
from polytool.core.errors import PolytoolError
from polytool.core.io import read_text, write_text

app = typer.Typer(
    name="text",
    help="Text utilities (diff, wc, case, slugify, md).",
    no_args_is_help=True,
)


@app.command("diff")
def cmd_diff(
    a: Annotated[Path, typer.Argument(help="First file")],
    b: Annotated[Path, typer.Argument(help="Second file")],
    unified: Annotated[int, typer.Option("--unified", "-u", help="Unified context lines")] = 3,
) -> None:
    """Show a unified diff between two text files.

    Examples:

        pt text diff a.txt b.txt
        pt text diff a.txt b.txt --unified 5
    """
    if not a.exists():
        raise PolytoolError(f"File not found: {a}")
    if not b.exists():
        raise PolytoolError(f"File not found: {b}")
    a_lines = a.read_text(encoding="utf-8").splitlines(keepends=True)
    b_lines = b.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = difflib.unified_diff(a_lines, b_lines, fromfile=str(a), tofile=str(b), n=unified)
    typer.echo("".join(diff), nl=False)


@app.command("wc")
def cmd_wc(
    source: Annotated[Path | None, typer.Argument(help="File path (or omit for stdin)")] = None,
) -> None:
    """Count lines, words, and characters.

    Examples:

        pt text wc README.md
        cat README.md | pt text wc
    """
    text = read_text(source)
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    words = len(text.split())
    chars = len(text)
    typer.echo(f"lines: {lines}\nwords: {words}\nchars: {chars}")


CASE_FNS = {
    "snake": lambda s: (
        re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).replace("-", "_").replace(" ", "_").lower()
    ),
    "kebab": lambda s: (
        re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s).replace("_", "-").replace(" ", "-").lower()
    ),
    "camel": None,  # filled below
    "pascal": None,
    "constant": lambda s: (
        re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).replace("-", "_").replace(" ", "_").upper()
    ),
    "title": str.title,
    "upper": str.upper,
    "lower": str.lower,
}


def _to_camel(s: str) -> str:
    parts = re.split(r"[\s_\-]+", s)
    if not parts:
        return ""
    head = parts[0].lower()
    return head + "".join(w.capitalize() for w in parts[1:])


def _to_pascal(s: str) -> str:
    parts = re.split(r"[\s_\-]+", s)
    return "".join(w.capitalize() for w in parts)


CASE_FNS["camel"] = _to_camel
CASE_FNS["pascal"] = _to_pascal


@app.command("case")
def cmd_case(
    style: Annotated[
        str,
        typer.Argument(help="snake | kebab | camel | pascal | constant | title | upper | lower"),
    ],
    text: Annotated[str | None, typer.Argument(help="Text (or omit for stdin)")] = None,
) -> None:
    """Convert string casing.

    Examples:

        pt text case snake "Hello World"
        pt text case camel "user-id-token"
        pt text case constant "fooBarBaz"
    """
    fn = CASE_FNS.get(style.lower())
    if fn is None:
        raise PolytoolError(
            f"Unknown style {style!r}",
            hint=f"One of: {', '.join(CASE_FNS)}",
        )
    payload = text if text is not None else read_text(None).rstrip("\n")
    typer.echo(fn(payload))


@app.command("slugify")
def cmd_slugify(
    text: Annotated[str | None, typer.Argument(help="Text (or omit for stdin)")] = None,
    separator: Annotated[str, typer.Option("--sep", help="Separator")] = "-",
) -> None:
    """URL-friendly slug from arbitrary text.

    Examples:

        pt text slugify "Hello, World! Café"
        echo "My Post Title" | pt text slugify --sep _
    """
    from slugify import slugify as _slugify

    payload = text if text is not None else read_text(None).rstrip("\n")
    typer.echo(_slugify(payload, separator=separator))


@app.command("md-to-html")
def cmd_md_to_html(
    source: Annotated[Path | None, typer.Argument(help="Markdown file (or '-' for stdin)")] = None,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Output file (default: stdout)")
    ] = None,
) -> None:
    """Convert Markdown to HTML.

    Examples:

        pt text md-to-html README.md -o README.html
        cat post.md | pt text md-to-html
    """
    from markdown_it import MarkdownIt

    md = MarkdownIt("commonmark", {"html": True}).enable("table").enable("strikethrough")
    rendered = md.render(read_text(source))
    write_text(output, rendered)


@app.command("md-preview")
def cmd_md_preview(
    source: Annotated[Path | None, typer.Argument(help="Markdown file (or '-' for stdin)")] = None,
) -> None:
    """Render Markdown in the terminal.

    Examples:

        pt text md-preview README.md
    """
    from rich.markdown import Markdown

    console.print(Markdown(read_text(source)))

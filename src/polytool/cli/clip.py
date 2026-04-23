"""Clipboard read/write."""

from __future__ import annotations

from typing import Annotated

import typer

from polytool.core.errors import PolytoolError
from polytool.core.io import read_text

app = typer.Typer(
    name="clip",
    help="Clipboard read/write.",
    no_args_is_help=True,
)


def _pyperclip():
    try:
        import pyperclip  # type: ignore

        return pyperclip
    except ImportError as exc:  # pragma: no cover
        raise PolytoolError(
            "pyperclip is missing.",
            hint="Reinstall polytool to restore base deps.",
        ) from exc


@app.command("copy")
def cmd_copy(
    text: Annotated[
        str | None, typer.Argument(help="Text (or omit to read stdin).")
    ] = None,
) -> None:
    """Copy text to the system clipboard.

    Examples:

        pt clip copy "hello"
        cat secret.txt | pt clip copy
    """
    payload = text if text is not None else read_text(None).rstrip("\n")
    pc = _pyperclip()
    try:
        pc.copy(payload)
    except pc.PyperclipException as exc:
        raise PolytoolError(
            f"Clipboard not available: {exc}",
            hint="On Linux, install xclip or xsel: 'apt install xclip'.",
        ) from exc
    typer.echo(f"Copied {len(payload)} chars.", err=True)


@app.command("paste")
def cmd_paste() -> None:
    """Print the clipboard contents to stdout.

    Examples:

        pt clip paste
        pt clip paste > out.txt
    """
    pc = _pyperclip()
    try:
        text = pc.paste()
    except pc.PyperclipException as exc:
        raise PolytoolError(
            f"Clipboard not available: {exc}",
            hint="On Linux, install xclip or xsel: 'apt install xclip'.",
        ) from exc
    typer.echo(text, nl=False)

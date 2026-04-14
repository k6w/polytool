"""I/O helpers — read from path or stdin, write to path or stdout."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import BinaryIO, TextIO


def read_text(source: Path | str | None) -> str:
    """Read text from a path, '-' (stdin), or None (stdin)."""
    if source is None or str(source) == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8")


def read_bytes(source: Path | str | None) -> bytes:
    """Read bytes from a path, '-' (stdin), or None (stdin)."""
    if source is None or str(source) == "-":
        return sys.stdin.buffer.read()
    return Path(source).read_bytes()


def write_text(target: Path | str | None, data: str) -> None:
    """Write text to a path, '-' (stdout), or None (stdout)."""
    if target is None or str(target) == "-":
        sys.stdout.write(data)
        if not data.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.flush()
        return
    Path(target).write_text(data, encoding="utf-8")


def write_bytes(target: Path | str, data: bytes) -> None:
    """Write bytes to a path. Use '-' to write to stdout buffer."""
    if str(target) == "-":
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        return
    Path(target).write_bytes(data)


def default_output(input_path: Path, new_suffix: str) -> Path:
    """Suggest an output path next to the input with a new suffix.

    >>> default_output(Path("/tmp/photo.png"), ".jpg")
    PosixPath('/tmp/photo.jpg')
    """
    return input_path.with_suffix(new_suffix if new_suffix.startswith(".") else f".{new_suffix}")


def open_input_binary(source: Path | str | None) -> BinaryIO:
    """Open a binary stream from path or stdin. Caller must close (except stdin)."""
    if source is None or str(source) == "-":
        return sys.stdin.buffer
    return Path(source).open("rb")


def open_output_binary(target: Path | str) -> BinaryIO:
    """Open a binary stream to path or stdout. Caller must close (except stdout)."""
    if str(target) == "-":
        return sys.stdout.buffer
    return Path(target).open("wb")


def open_input_text(source: Path | str | None) -> TextIO:
    """Open a text stream from path or stdin."""
    if source is None or str(source) == "-":
        return sys.stdin
    return Path(source).open("r", encoding="utf-8")

"""Lazy-import helper — load optional deps on demand with a friendly error.

Subcommand verbs that need an optional library should call:

    rembg = require_extra("rembg", extra="ai")

If the import fails, a `MissingExtraError` is raised, which the CLI renders
as a red panel with the exact `uv tool install` command.
"""

from __future__ import annotations

import importlib
from types import ModuleType

from polytool.core.errors import MissingExtraError


def require_extra(module: str, extra: str) -> ModuleType:
    """Import *module*, or raise MissingExtraError pointing at *extra*.

    >>> # require_extra("rembg", extra="ai")  # raises if rembg isn't installed
    """
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise MissingExtraError(module, extra) from exc


def try_import(module: str) -> ModuleType | None:
    """Try to import a module; return None on failure (no error)."""
    try:
        return importlib.import_module(module)
    except ImportError:
        return None

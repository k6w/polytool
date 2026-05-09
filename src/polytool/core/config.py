"""Persistent user config for polytool, stored as TOML at ``~/.polytool/config.toml``.

Tiny stdlib-only key-value store (read with ``tomllib``, write with ``tomli_w``).
Used so per-user preferences survive across invocations — e.g. which browser
``pt dl`` should pull cookies from.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomli_w

CONFIG_DIR = Path.home() / ".polytool"
CONFIG_PATH = CONFIG_DIR / "config.toml"


def _resolve() -> tuple[Path, Path]:
    """Return the (dir, file) pair currently in use.

    Indirection so tests can monkeypatch CONFIG_PATH and have ``save()`` honor it.
    """
    return CONFIG_PATH.parent, CONFIG_PATH


def load() -> dict[str, Any]:
    """Read the config file. Returns ``{}`` if missing or unreadable."""
    _, path = _resolve()
    if not path.exists():
        return {}
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def save(data: dict[str, Any]) -> None:
    """Write the full config dict (creates parent dir if needed)."""
    parent, path = _resolve()
    parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomli_w.dumps(data), encoding="utf-8")


def get(*keys: str, default: Any = None) -> Any:
    """Read a nested key. ``get("dl", "cookies_from_browser")`` returns
    ``data['dl']['cookies_from_browser']`` or ``default``.
    """
    cur: Any = load()
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def set_(value: Any, *keys: str) -> None:
    """Set a nested key, creating intermediate tables as needed."""
    if not keys:
        raise ValueError("At least one key required")
    data = load()
    cur: dict[str, Any] = data
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value
    save(data)


def unset(*keys: str) -> None:
    """Delete a nested key. Silent no-op if the key is missing."""
    if not keys:
        return
    data = load()
    cur: Any = data
    for k in keys[:-1]:
        if not isinstance(cur, dict) or k not in cur:
            return
        cur = cur[k]
    if isinstance(cur, dict) and keys[-1] in cur:
        del cur[keys[-1]]
        save(data)

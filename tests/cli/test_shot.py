"""Tests for `pt shot` — only smoke-tests the screen-capture path.

Web capture requires Chromium and is gated behind --install; we don't run
that in the standard test run. Screen capture also fails on headless CI,
so we skip if no display is available.
"""

from __future__ import annotations

import os

import pytest

mss_mod = pytest.importorskip("mss")


def _has_display() -> bool:
    if os.name == "nt":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


pytestmark = pytest.mark.skipif(not _has_display(), reason="No display for screenshot")


def test_screen_capture(runner, cli_app, tmp_path) -> None:
    out = tmp_path / "shot.png"
    result = runner.invoke(cli_app, ["shot", "screen", "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert out.read_bytes()[:4] == b"\x89PNG"


def test_screen_bad_monitor(runner, cli_app, tmp_path) -> None:
    out = tmp_path / "x.png"
    result = runner.invoke(
        cli_app, ["shot", "screen", "--monitor", "999", "-o", str(out)]
    )
    assert result.exit_code != 0

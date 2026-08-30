"""Tests for `pt clip`. Skipped on headless Linux where clipboard isn't available."""

from __future__ import annotations

import pytest


def _clipboard_available() -> bool:
    try:
        import pyperclip

        original = pyperclip.paste()
        probe = "polytool-clipboard-availability-probe"
        pyperclip.copy(probe)
        available = pyperclip.paste() == probe
        pyperclip.copy(original)
        return available
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _clipboard_available(),
    reason="System clipboard not available (likely headless Linux without xclip).",
)


def test_copy_paste_roundtrip(runner, cli_app) -> None:
    payload = "polytool-clip-test-string"
    cp = runner.invoke(cli_app, ["clip", "copy", payload])
    assert cp.exit_code == 0
    out = runner.invoke(cli_app, ["clip", "paste"])
    assert out.exit_code == 0
    assert payload in out.stdout

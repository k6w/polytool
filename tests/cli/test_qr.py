"""Tests for `pt qr`."""

from __future__ import annotations

from pathlib import Path


def test_gen_png(runner, cli_app, tmp_path) -> None:
    out = tmp_path / "qr.png"
    result = runner.invoke(cli_app, ["qr", "gen", "https://example.com", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    # Sanity: PNG magic
    assert out.read_bytes()[:4] == b"\x89PNG"


def test_gen_svg(runner, cli_app, tmp_path) -> None:
    out = tmp_path / "qr.svg"
    result = runner.invoke(cli_app, ["qr", "gen", "hi", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("<?xml") or "<svg" in out.read_text(encoding="utf-8")


def test_gen_terminal(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["qr", "gen", "x", "--terminal"])
    assert result.exit_code == 0


def test_gen_unsupported_ext(runner, cli_app, tmp_path) -> None:
    out = tmp_path / "qr.bogus"
    result = runner.invoke(cli_app, ["qr", "gen", "x", "--output", str(out)])
    assert result.exit_code != 0


def test_wifi(runner, cli_app, tmp_path) -> None:
    out = tmp_path / "wifi.png"
    result = runner.invoke(
        cli_app,
        ["qr", "wifi", "MyNet", "--password", "hunter2", "--output", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()


def test_decode_missing_file(runner, cli_app, tmp_path) -> None:
    result = runner.invoke(cli_app, ["qr", "decode", str(tmp_path / "nope.png")])
    assert result.exit_code != 0

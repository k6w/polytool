"""Tests for `pt color`."""

from __future__ import annotations


def test_hex_to_all(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["color", "convert", "#3366ff"])
    assert result.exit_code == 0
    assert "rgb(51, 102, 255)" in result.stdout
    assert "hex" in result.stdout
    assert "hsl" in result.stdout
    assert "cmyk" in result.stdout


def test_hex_short_form(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["color", "convert", "#f00", "--to", "rgb"])
    assert result.exit_code == 0
    assert "rgb(255, 0, 0)" in result.stdout


def test_rgb_to_hsl(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["color", "convert", "rgb(51,102,255)", "--to", "hsl"])
    assert result.exit_code == 0
    assert "hsl" in result.stdout


def test_unknown_target(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["color", "convert", "#fff", "--to", "bogus"])
    assert result.exit_code != 0


def test_invalid_color(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["color", "convert", "not-a-color"])
    assert result.exit_code != 0

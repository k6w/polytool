"""Tests for `pt convert`."""

from __future__ import annotations


def test_unit_km_to_mi(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["convert", "unit", "100 km", "--to", "mi"])
    assert result.exit_code == 0
    # 100 km ≈ 62.137 mi
    assert "62" in result.stdout


def test_unit_celsius_to_fahrenheit(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["convert", "unit", "100 degC", "--to", "degF"])
    assert result.exit_code == 0
    # 100°C = 212°F
    assert "212" in result.stdout


def test_unit_invalid(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["convert", "unit", "100 banana", "--to", "mi"])
    assert result.exit_code != 0


def test_timestamp_epoch_to_iso(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["convert", "timestamp", "0"])
    assert result.exit_code == 0
    assert "1970-01-01" in result.stdout


def test_timestamp_iso_to_epoch(runner, cli_app) -> None:
    result = runner.invoke(
        cli_app, ["convert", "timestamp", "1970-01-01T00:00:00Z", "--to", "epoch"]
    )
    assert result.exit_code == 0
    assert result.stdout.strip() == "0"


def test_timestamp_invalid(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["convert", "timestamp", "not-a-date"])
    assert result.exit_code != 0


def test_base_hex_to_dec(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["convert", "base", "0xff", "--to", "dec"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "255"


def test_base_dec_to_hex(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["convert", "base", "255", "--to", "hex"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "ff"


def test_base_explicit_from(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["convert", "base", "11111111", "--from", "2", "--to", "dec"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "255"

"""Tests for `pt cron`."""

from __future__ import annotations


def test_explain_simple(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["cron", "explain", "0 9 * * MON"])
    assert result.exit_code == 0
    text = result.stdout.lower()
    assert "monday" in text
    assert "9" in text or "09" in text


def test_explain_invalid(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["cron", "explain", "not a cron"])
    assert result.exit_code != 0


def test_next_count(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["cron", "next", "0 9 * * MON", "--count", "4"])
    assert result.exit_code == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 4


def test_next_invalid(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["cron", "next", "??"])
    assert result.exit_code != 0

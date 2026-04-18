"""Tests for `pt gen` (password, uuid, lorem)."""

from __future__ import annotations

import re
import uuid as _uuid


def test_password_default_length(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["gen", "password"])
    assert result.exit_code == 0
    pw = result.stdout.strip()
    assert len(pw) == 24


def test_password_custom_length_and_count(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["gen", "password", "--length", "32", "--count", "3"])
    assert result.exit_code == 0
    lines = [line for line in result.stdout.splitlines() if line]
    assert len(lines) == 3
    assert all(len(line) == 32 for line in lines)


def test_password_no_symbols(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["gen", "password", "--no-symbols", "--length", "40"])
    assert result.exit_code == 0
    pw = result.stdout.strip()
    assert pw.isalnum()


def test_password_min_length_error(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["gen", "password", "--length", "2"])
    assert result.exit_code != 0


def test_uuid_v4(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["gen", "uuid", "v4"])
    assert result.exit_code == 0
    parsed = _uuid.UUID(result.stdout.strip())
    assert parsed.version == 4


def test_uuid_v5(runner, cli_app) -> None:
    result = runner.invoke(
        cli_app,
        ["gen", "uuid", "v5", "--namespace", "dns", "--name", "example.com"],
    )
    assert result.exit_code == 0
    parsed = _uuid.UUID(result.stdout.strip())
    assert parsed.version == 5


def test_uuid_unknown_version(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["gen", "uuid", "v99"])
    assert result.exit_code != 0


def test_lorem_default(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["gen", "lorem"])
    assert result.exit_code == 0
    assert len(result.stdout.split()) >= 5


def test_lorem_words_count(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["gen", "lorem", "--words", "12"])
    assert result.exit_code == 0
    words = re.findall(r"\S+", result.stdout)
    assert len(words) == 12

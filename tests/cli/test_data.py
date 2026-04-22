"""Tests for `pt data` (json/yaml/toml/csv/xml)."""

from __future__ import annotations

import json


def test_json_to_yaml(runner, cli_app, tmp_path) -> None:
    src = tmp_path / "x.json"
    src.write_text(json.dumps({"name": "polytool", "tags": ["cli", "utility"]}), encoding="utf-8")
    result = runner.invoke(cli_app, ["data", "convert", str(src), "--to", "yaml"])
    assert result.exit_code == 0
    assert "name: polytool" in result.stdout
    assert "- cli" in result.stdout


def test_yaml_to_json(runner, cli_app, tmp_path) -> None:
    src = tmp_path / "x.yaml"
    src.write_text("name: polytool\ntags:\n  - cli\n  - utility\n", encoding="utf-8")
    result = runner.invoke(cli_app, ["data", "convert", str(src), "--to", "json"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed == {"name": "polytool", "tags": ["cli", "utility"]}


def test_toml_to_json(runner, cli_app, tmp_path) -> None:
    src = tmp_path / "x.toml"
    src.write_text('name = "polytool"\nver = "0.1.0"\n', encoding="utf-8")
    result = runner.invoke(cli_app, ["data", "convert", str(src), "--to", "json"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["name"] == "polytool"


def test_csv_to_json(runner, cli_app, tmp_path) -> None:
    src = tmp_path / "x.csv"
    src.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")
    result = runner.invoke(cli_app, ["data", "convert", str(src), "--to", "json"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed == [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]


def test_pretty(runner, cli_app, tmp_path) -> None:
    src = tmp_path / "x.json"
    src.write_text('{"a":1,"b":[1,2,3]}', encoding="utf-8")
    result = runner.invoke(cli_app, ["data", "pretty", str(src)])
    assert result.exit_code == 0
    assert "  " in result.stdout  # indented


def test_validate_ok(runner, cli_app, tmp_path) -> None:
    src = tmp_path / "x.json"
    src.write_text('{"a": 1}', encoding="utf-8")
    result = runner.invoke(cli_app, ["data", "validate", str(src)])
    assert result.exit_code == 0


def test_validate_bad(runner, cli_app, tmp_path) -> None:
    src = tmp_path / "x.json"
    src.write_text("{not valid json", encoding="utf-8")
    result = runner.invoke(cli_app, ["data", "validate", str(src)])
    assert result.exit_code != 0


def test_unknown_target(runner, cli_app, tmp_path) -> None:
    src = tmp_path / "x.json"
    src.write_text("{}", encoding="utf-8")
    result = runner.invoke(cli_app, ["data", "convert", str(src), "--to", "bogus"])
    assert result.exit_code != 0

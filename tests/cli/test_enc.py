"""Tests for `pt enc` (hash / base64 / url / html / jwt)."""

from __future__ import annotations

import base64
import hashlib

import jwt


def test_hash_sha256(runner, cli_app, tmp_path) -> None:
    p = tmp_path / "x.txt"
    p.write_bytes(b"hello")
    expected = hashlib.sha256(b"hello").hexdigest()
    result = runner.invoke(cli_app, ["enc", "hash", "sha256", str(p)])
    assert result.exit_code == 0
    assert expected in result.stdout


def test_hash_xxhash(runner, cli_app, tmp_path) -> None:
    p = tmp_path / "x.txt"
    p.write_bytes(b"hello")
    result = runner.invoke(cli_app, ["enc", "hash", "xxhash", str(p)])
    assert result.exit_code == 0
    assert len(result.stdout.strip()) == 16  # xxh3_64 = 16 hex chars


def test_hash_unknown_algorithm(runner, cli_app, tmp_path) -> None:
    p = tmp_path / "x.txt"
    p.write_bytes(b"hi")
    result = runner.invoke(cli_app, ["enc", "hash", "bogus", str(p)])
    assert result.exit_code != 0


def test_base64_encode_decode_roundtrip(runner, cli_app, tmp_path) -> None:
    p = tmp_path / "x.bin"
    p.write_bytes(b"\x00\x01\x02hello")
    enc = runner.invoke(cli_app, ["enc", "base64", "encode", str(p)])
    assert enc.exit_code == 0
    assert enc.stdout.strip() == base64.b64encode(b"\x00\x01\x02hello").decode("ascii")


def test_url_encode(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["enc", "url", "encode", "hello world & friends"])
    assert result.exit_code == 0
    assert "%20" in result.stdout and "%26" in result.stdout


def test_html_encode(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["enc", "html", "encode", "<b>"])
    assert result.exit_code == 0
    assert "&lt;" in result.stdout and "&gt;" in result.stdout


def test_jwt_decode(runner, cli_app) -> None:
    token = jwt.encode({"sub": "42", "role": "admin"}, "secret", algorithm="HS256")
    result = runner.invoke(cli_app, ["enc", "jwt-decode", token])
    assert result.exit_code == 0
    assert "Header" in result.stdout
    assert "Payload" in result.stdout


def test_jwt_decode_invalid(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["enc", "jwt-decode", "not.a.token"])
    assert result.exit_code != 0


def test_jwt_verify_ok(runner, cli_app) -> None:
    token = jwt.encode({"sub": "x"}, "topsecret", algorithm="HS256")
    result = runner.invoke(cli_app, ["enc", "jwt-verify", token, "--secret", "topsecret"])
    assert result.exit_code == 0
    assert "Signature OK" in result.stdout


def test_jwt_verify_bad_secret(runner, cli_app) -> None:
    token = jwt.encode({"sub": "x"}, "right", algorithm="HS256")
    result = runner.invoke(cli_app, ["enc", "jwt-verify", token, "--secret", "wrong"])
    assert result.exit_code != 0

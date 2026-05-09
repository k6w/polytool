"""Tests for `pt dl` — yt-dlp is mocked so tests don't hit the network."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("yt_dlp")


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Point polytool's config to a tmp file so the real ~/.polytool isn't touched."""
    from polytool.core import config as cfg

    fake = tmp_path / "config.toml"
    monkeypatch.setattr(cfg, "CONFIG_PATH", fake)
    return fake


def _install_fake_ydl(monkeypatch, captured: dict, *, info=None, raise_dl_error=None):
    import yt_dlp

    class FakeYDL:
        def __init__(self, opts):
            captured["opts"] = opts

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def download(self, urls):
            captured["urls"] = list(urls)
            if raise_dl_error:
                raise yt_dlp.utils.DownloadError(raise_dl_error)

        def extract_info(self, url, download):
            captured["urls"] = [url]
            if raise_dl_error:
                raise yt_dlp.utils.DownloadError(raise_dl_error)
            return info or {"title": "Example", "webpage_url": url}

    monkeypatch.setattr(yt_dlp, "YoutubeDL", FakeYDL)


def test_get_calls_ytdlp(runner, cli_app, monkeypatch, tmp_path, isolated_config) -> None:
    captured: dict = {}
    _install_fake_ydl(monkeypatch, captured)
    out = tmp_path / "downloads"
    result = runner.invoke(
        cli_app,
        ["dl", "get", "https://example.com/x", "-o", str(out), "--audio-only"],
    )
    assert result.exit_code == 0, result.output
    assert captured["urls"] == ["https://example.com/x"]
    pps = captured["opts"]["postprocessors"]
    assert any(pp["key"] == "FFmpegExtractAudio" for pp in pps)
    assert captured["opts"]["format"] == "bestaudio/best"


def test_info_calls_ytdlp(runner, cli_app, monkeypatch, isolated_config) -> None:
    captured: dict = {}
    _install_fake_ydl(
        monkeypatch,
        captured,
        info={"title": "Example", "uploader": "TestChannel", "duration": 42, "webpage_url": "x"},
    )
    result = runner.invoke(cli_app, ["dl", "info", "https://example.com/x"])
    assert result.exit_code == 0
    assert "Example" in result.stdout
    assert "TestChannel" in result.stdout


def test_get_error_with_bot_hint(runner, cli_app, monkeypatch, isolated_config) -> None:
    captured: dict = {}
    _install_fake_ydl(
        monkeypatch,
        captured,
        raise_dl_error="Sign in to confirm you're not a bot.",
    )
    result = runner.invoke(cli_app, ["dl", "get", "https://example.com/x"])
    assert result.exit_code != 0


def test_setup_show_empty(runner, cli_app, isolated_config) -> None:
    result = runner.invoke(cli_app, ["dl", "setup", "--show"])
    assert result.exit_code == 0
    assert "No saved" in result.stdout


def test_setup_save_browser(runner, cli_app, isolated_config) -> None:
    result = runner.invoke(cli_app, ["dl", "setup", "--browser", "firefox"])
    assert result.exit_code == 0
    assert "firefox" in result.stdout
    # Confirm persisted
    show = runner.invoke(cli_app, ["dl", "setup", "--show"])
    assert show.exit_code == 0
    assert "firefox" in show.stdout


def test_setup_save_browser_with_profile(runner, cli_app, isolated_config) -> None:
    result = runner.invoke(cli_app, ["dl", "setup", "--browser", "chrome:Default"])
    assert result.exit_code == 0


def test_setup_save_cookies_file(runner, cli_app, isolated_config, tmp_path) -> None:
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    result = runner.invoke(cli_app, ["dl", "setup", "--cookies", str(cookies)])
    assert result.exit_code == 0


def test_setup_cookies_file_missing(runner, cli_app, isolated_config, tmp_path) -> None:
    result = runner.invoke(cli_app, ["dl", "setup", "--cookies", str(tmp_path / "nope.txt")])
    assert result.exit_code != 0


def test_setup_clear(runner, cli_app, isolated_config) -> None:
    runner.invoke(cli_app, ["dl", "setup", "--browser", "firefox"])
    result = runner.invoke(cli_app, ["dl", "setup", "--clear"])
    assert result.exit_code == 0
    show = runner.invoke(cli_app, ["dl", "setup", "--show"])
    assert "No saved" in show.stdout


def test_setup_browser_xor_cookies(runner, cli_app, isolated_config, tmp_path) -> None:
    f = tmp_path / "c.txt"
    f.write_text("", encoding="utf-8")
    result = runner.invoke(cli_app, ["dl", "setup", "--browser", "firefox", "--cookies", str(f)])
    assert result.exit_code != 0


def test_get_uses_saved_config(runner, cli_app, monkeypatch, isolated_config) -> None:
    """After setup, dl get/info auto-applies the saved cookies."""
    runner.invoke(cli_app, ["dl", "setup", "--browser", "firefox"])

    captured: dict = {}
    _install_fake_ydl(monkeypatch, captured)
    result = runner.invoke(cli_app, ["dl", "get", "https://example.com/x"])
    assert result.exit_code == 0, result.output
    assert "cookiesfrombrowser" in captured["opts"]
    spec = captured["opts"]["cookiesfrombrowser"]
    assert spec[0] == "firefox"


def test_get_cli_flag_overrides_config(runner, cli_app, monkeypatch, isolated_config) -> None:
    runner.invoke(cli_app, ["dl", "setup", "--browser", "firefox"])

    captured: dict = {}
    _install_fake_ydl(monkeypatch, captured)
    result = runner.invoke(
        cli_app,
        ["dl", "get", "https://example.com/x", "--cookies-from-browser", "chrome"],
    )
    assert result.exit_code == 0, result.output
    assert captured["opts"]["cookiesfrombrowser"][0] == "chrome"


def test_info_uses_saved_config(runner, cli_app, monkeypatch, isolated_config) -> None:
    runner.invoke(cli_app, ["dl", "setup", "--browser", "edge"])

    captured: dict = {}
    _install_fake_ydl(monkeypatch, captured, info={"title": "Example", "webpage_url": "x"})
    result = runner.invoke(cli_app, ["dl", "info", "https://example.com/x"])
    assert result.exit_code == 0
    assert captured["opts"]["cookiesfrombrowser"][0] == "edge"


def test_browser_spec_parser() -> None:
    from polytool.cli.dl import _parse_browser_spec

    assert _parse_browser_spec("chrome") == ("chrome", None, None, None)
    assert _parse_browser_spec("firefox:default") == ("firefox", "default", None, None)
    assert _parse_browser_spec("firefox+gnomekeyring:default::personal") == (
        "firefox",
        "default",
        "gnomekeyring",
        "personal",
    )


def test_get_username_password(runner, cli_app, monkeypatch, isolated_config) -> None:
    captured: dict = {}
    _install_fake_ydl(monkeypatch, captured)
    result = runner.invoke(
        cli_app,
        [
            "dl",
            "get",
            "https://example.com/x",
            "--username",
            "alice",
            "--password",
            "hunter2",
            "--video-password",
            "vid-pwd",
        ],
    )
    assert result.exit_code == 0, result.output
    assert captured["opts"]["username"] == "alice"
    assert captured["opts"]["password"] == "hunter2"
    assert captured["opts"]["videopassword"] == "vid-pwd"


def test_info_username_password(runner, cli_app, monkeypatch, isolated_config) -> None:
    captured: dict = {}
    _install_fake_ydl(monkeypatch, captured, info={"title": "X", "webpage_url": "u"})
    result = runner.invoke(
        cli_app,
        ["dl", "info", "https://example.com/x", "-u", "alice", "-p", "hunter2"],
    )
    assert result.exit_code == 0, result.output
    assert captured["opts"]["username"] == "alice"
    assert captured["opts"]["password"] == "hunter2"


def test_xor_cookies_runtime(runner, cli_app, monkeypatch, isolated_config) -> None:
    captured: dict = {}
    _install_fake_ydl(monkeypatch, captured)
    result = runner.invoke(
        cli_app,
        [
            "dl",
            "get",
            "https://example.com/x",
            "--cookies-from-browser",
            "firefox",
            "--cookies",
            "C:/nope.txt" if Path("C:/").exists() else "/tmp/nope.txt",
        ],
    )
    assert result.exit_code != 0

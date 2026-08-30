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
    from yt_dlp.utils import DownloadError

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
                raise DownloadError(raise_dl_error)

        def extract_info(self, url, download=True, process=True, **_kwargs):
            captured["urls"] = [url]
            captured["process"] = process
            if raise_dl_error:
                raise DownloadError(raise_dl_error)
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
    assert "extractor_args" not in captured["opts"]


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
    # Info should bypass format processing.
    assert captured["process"] is False
    assert "extractor_args" not in captured["opts"]


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


def test_unknown_browser_rejected() -> None:
    from polytool.cli.dl import _parse_browser_spec
    from polytool.core.errors import PolytoolError

    with pytest.raises(PolytoolError):
        _parse_browser_spec("not-a-real-browser")


def _make_fake_firefox_dir(root: Path, profile_name: str = "default") -> tuple[Path, Path]:
    """Build a synthetic Firefox-fork data dir with a profiles.ini default profile."""
    profile_dir = root / f"abcd1234.{profile_name}"
    profile_dir.mkdir(parents=True)
    ini = root / "profiles.ini"
    ini.write_text(
        f"[Profile0]\nName={profile_name}\nIsRelative=1\nPath={profile_dir.name}\nDefault=1\n"
        "\n[Install01]\nDefault=" + profile_dir.name + "\nLocked=1\n",
        encoding="utf-8",
    )
    return root, profile_dir


def test_zen_resolution(monkeypatch, tmp_path) -> None:
    """`pt dl setup --browser zen` should yield ('firefox', <profile-path>, ...)."""
    data_dir, profile_dir = _make_fake_firefox_dir(tmp_path / "zen")

    from polytool.cli import dl as dl_mod

    monkeypatch.setattr(
        dl_mod,
        "find_firefox_fork_data_dir",
        lambda name: data_dir if name == "zen" else None,
    )

    from polytool.cli.dl import _parse_browser_spec

    result = _parse_browser_spec("zen")
    assert result[0] == "firefox"
    assert result[1] == str(profile_dir)


def test_zen_with_named_profile(monkeypatch, tmp_path) -> None:
    data_dir, _ = _make_fake_firefox_dir(tmp_path / "zen", profile_name="default")
    # Add a second profile.
    extra = data_dir / "xyz789.work"
    extra.mkdir()
    ini = data_dir / "profiles.ini"
    ini.write_text(
        ini.read_text(encoding="utf-8")
        + f"\n[Profile1]\nName=work\nIsRelative=1\nPath={extra.name}\n",
        encoding="utf-8",
    )

    from polytool.cli import dl as dl_mod

    monkeypatch.setattr(
        dl_mod,
        "find_firefox_fork_data_dir",
        lambda name: data_dir if name == "zen" else None,
    )

    from polytool.cli.dl import _parse_browser_spec

    result = _parse_browser_spec("zen:work")
    assert result[0] == "firefox"
    assert result[1] == str(extra)


def test_zen_not_installed(monkeypatch) -> None:
    from polytool.cli import dl as dl_mod
    from polytool.core.errors import PolytoolError

    monkeypatch.setattr(dl_mod, "find_firefox_fork_data_dir", lambda name: None)

    with pytest.raises(PolytoolError):
        dl_mod._parse_browser_spec("zen")


def test_librewolf_resolution(monkeypatch, tmp_path) -> None:
    data_dir, profile_dir = _make_fake_firefox_dir(tmp_path / "librewolf")
    from polytool.cli import dl as dl_mod

    monkeypatch.setattr(
        dl_mod,
        "find_firefox_fork_data_dir",
        lambda name: data_dir if name == "librewolf" else None,
    )

    result = dl_mod._parse_browser_spec("librewolf")
    assert result[0] == "firefox"
    assert result[1] == str(profile_dir)


def test_supported_browsers_includes_forks() -> None:
    from polytool.cli.dl import SUPPORTED_BROWSERS

    for fork in ("zen", "librewolf", "waterfox", "floorp", "mullvad"):
        assert fork in SUPPORTED_BROWSERS


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

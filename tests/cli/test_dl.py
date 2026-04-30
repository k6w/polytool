"""Tests for `pt dl` — yt-dlp is mocked so tests don't hit the network."""

from __future__ import annotations

import pytest

pytest.importorskip("yt_dlp")


def test_get_calls_ytdlp(runner, cli_app, monkeypatch, tmp_path) -> None:
    """Verify our wrapper passes args correctly to yt_dlp.YoutubeDL."""
    import yt_dlp

    captured = {}

    class FakeYDL:
        def __init__(self, opts):
            captured["opts"] = opts

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def download(self, urls):
            captured["urls"] = list(urls)

    monkeypatch.setattr(yt_dlp, "YoutubeDL", FakeYDL)
    out = tmp_path / "downloads"
    result = runner.invoke(
        cli_app,
        ["dl", "get", "https://example.com/x", "-o", str(out), "--audio-only"],
    )
    assert result.exit_code == 0, result.output
    assert captured["urls"] == ["https://example.com/x"]
    # audio-only should add the FFmpegExtractAudio postprocessor
    pps = captured["opts"]["postprocessors"]
    assert any(pp["key"] == "FFmpegExtractAudio" for pp in pps)
    assert captured["opts"]["format"] == "bestaudio/best"


def test_info_calls_ytdlp(runner, cli_app, monkeypatch) -> None:
    import yt_dlp

    class FakeYDL:
        def __init__(self, opts):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, url, download):
            assert download is False
            return {
                "title": "Example",
                "uploader": "TestChannel",
                "duration": 42,
                "webpage_url": url,
            }

    monkeypatch.setattr(yt_dlp, "YoutubeDL", FakeYDL)
    result = runner.invoke(cli_app, ["dl", "info", "https://example.com/x"])
    assert result.exit_code == 0
    assert "Example" in result.stdout
    assert "TestChannel" in result.stdout


def test_get_error(runner, cli_app, monkeypatch) -> None:
    import yt_dlp

    class FakeYDL:
        def __init__(self, opts):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def download(self, urls):
            raise yt_dlp.utils.DownloadError("simulated")

    monkeypatch.setattr(yt_dlp, "YoutubeDL", FakeYDL)
    result = runner.invoke(cli_app, ["dl", "get", "https://example.com/x"])
    assert result.exit_code != 0

"""Tests for `pt vid` — uses real ffmpeg via imageio-ffmpeg or system."""

from __future__ import annotations

import shutil

import pytest

# Skip the whole module unless ffmpeg is reachable.
pytest.importorskip("imageio_ffmpeg")


def _ffmpeg_ok() -> bool:
    if shutil.which("ffmpeg"):
        return True
    try:
        from polytool.core.ffmpeg import ffmpeg_path

        return bool(ffmpeg_path())
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")


def test_convert_mp4_to_webm(runner, cli_app, tiny_mp4, tmp_path) -> None:
    out = tmp_path / "out.webm"
    result = runner.invoke(cli_app, ["vid", "convert", str(tiny_mp4), "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists() and out.stat().st_size > 0


def test_extract_audio(runner, cli_app, tiny_mp4, tmp_path) -> None:
    out = tmp_path / "audio.mp3"
    result = runner.invoke(cli_app, ["vid", "extract-audio", str(tiny_mp4), "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists() and out.stat().st_size > 0


def test_trim(runner, cli_app, tiny_mp4, tmp_path) -> None:
    out = tmp_path / "trim.mp4"
    result = runner.invoke(
        cli_app, ["vid", "trim", str(tiny_mp4), "-s", "0", "-d", "1", "-o", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert out.exists() and out.stat().st_size > 0


def test_gif(runner, cli_app, tiny_mp4, tmp_path) -> None:
    out = tmp_path / "out.gif"
    result = runner.invoke(
        cli_app,
        ["vid", "gif", str(tiny_mp4), "--fps", "10", "--width", "32", "-o", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert out.read_bytes()[:6] in (b"GIF87a", b"GIF89a")


def test_trim_conflict(runner, cli_app, tiny_mp4, tmp_path) -> None:
    result = runner.invoke(
        cli_app,
        ["vid", "trim", str(tiny_mp4), "-e", "0:01", "-d", "1"],
    )
    assert result.exit_code != 0


def test_missing_file(runner, cli_app, tmp_path) -> None:
    out = tmp_path / "x.mp4"
    result = runner.invoke(cli_app, ["vid", "convert", str(tmp_path / "nope.mp4"), "-o", str(out)])
    assert result.exit_code != 0

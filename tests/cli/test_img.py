"""Tests for `pt img`."""

from __future__ import annotations

import pytest

PIL = pytest.importorskip("PIL")


def test_convert_png_to_jpg(runner, cli_app, tiny_png) -> None:
    out = tiny_png.with_suffix(".jpg")
    result = runner.invoke(cli_app, ["img", "convert", str(tiny_png), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert out.read_bytes()[:3] == b"\xff\xd8\xff"  # JPEG magic


def test_convert_jpg_to_webp(runner, cli_app, tiny_jpg) -> None:
    result = runner.invoke(cli_app, ["img", "convert", str(tiny_jpg), "--to", "webp"])
    assert result.exit_code == 0
    assert tiny_jpg.with_suffix(".webp").exists()


def test_convert_missing_file(runner, cli_app, tmp_path) -> None:
    result = runner.invoke(cli_app, ["img", "convert", str(tmp_path / "nope.png"), "--to", "jpg"])
    assert result.exit_code != 0


def test_convert_no_output(runner, cli_app, tiny_png) -> None:
    result = runner.invoke(cli_app, ["img", "convert", str(tiny_png)])
    assert result.exit_code != 0


def test_resize_width(runner, cli_app, tiny_png) -> None:
    out = tiny_png.with_stem("resized")
    result = runner.invoke(
        cli_app, ["img", "resize", str(tiny_png), "--width", "16", "-o", str(out)]
    )
    assert result.exit_code == 0
    assert out.exists()
    from PIL import Image

    assert Image.open(out).size[0] == 16


def test_resize_percent(runner, cli_app, tiny_png) -> None:
    result = runner.invoke(cli_app, ["img", "resize", str(tiny_png), "--percent", "50"])
    assert result.exit_code == 0
    out = tiny_png.with_stem(tiny_png.stem + "_resized")
    assert out.exists()
    from PIL import Image

    assert Image.open(out).size == (16, 16)


def test_resize_no_args(runner, cli_app, tiny_png) -> None:
    result = runner.invoke(cli_app, ["img", "resize", str(tiny_png)])
    assert result.exit_code != 0


def test_compress(runner, cli_app, tiny_jpg) -> None:
    result = runner.invoke(cli_app, ["img", "compress", str(tiny_jpg), "-q", "30"])
    assert result.exit_code == 0
    out = tiny_jpg.with_stem(tiny_jpg.stem + "_compressed")
    assert out.exists()


def test_exif_view(runner, cli_app, tiny_jpg) -> None:
    result = runner.invoke(cli_app, ["img", "exif", str(tiny_jpg)])
    assert result.exit_code == 0


def test_exif_strip(runner, cli_app, tiny_jpg) -> None:
    result = runner.invoke(cli_app, ["img", "exif", str(tiny_jpg), "--strip"])
    assert result.exit_code == 0
    out = tiny_jpg.with_stem(tiny_jpg.stem + "_clean")
    assert out.exists()


def test_palette(runner, cli_app, tiny_png) -> None:
    result = runner.invoke(cli_app, ["img", "palette", str(tiny_png), "--count", "3"])
    assert result.exit_code == 0
    # ColorThief returns hex codes; just check output isn't empty
    assert "#" in result.stdout


def test_watermark(runner, cli_app, tiny_jpg) -> None:
    out = tiny_jpg.with_stem("wm")
    result = runner.invoke(
        cli_app,
        ["img", "watermark", str(tiny_jpg), "--text", "x", "-o", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()


def test_watermark_unknown_position(runner, cli_app, tiny_jpg) -> None:
    result = runner.invoke(
        cli_app,
        ["img", "watermark", str(tiny_jpg), "--position", "bogus"],
    )
    assert result.exit_code != 0

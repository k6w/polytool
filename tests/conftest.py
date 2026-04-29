"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from polytool.cli import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def runner() -> CliRunner:
    """A Typer CliRunner."""
    return CliRunner()


@pytest.fixture
def cli_app():
    return app


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def tiny_png(tmp_path: Path) -> Path:
    """A 32x32 RGB PNG with a simple pattern."""
    from PIL import Image, ImageDraw

    p = tmp_path / "tiny.png"
    img = Image.new("RGB", (32, 32), "white")
    d = ImageDraw.Draw(img)
    d.rectangle((4, 4, 27, 27), fill="red")
    d.ellipse((10, 10, 22, 22), fill="blue")
    img.save(p)
    return p


@pytest.fixture
def tiny_jpg(tmp_path: Path) -> Path:
    from PIL import Image

    p = tmp_path / "tiny.jpg"
    img = Image.new("RGB", (32, 32), "lightblue")
    img.save(p, quality=80)
    return p


@pytest.fixture
def tiny_pdf(tmp_path: Path) -> Path:
    """A 2-page PDF built on the fly with PyMuPDF."""
    import pymupdf

    p = tmp_path / "tiny.pdf"
    doc = pymupdf.open()
    for n in (1, 2):
        page = doc.new_page(width=200, height=200)
        page.insert_text((20, 30), f"page {n} hello world", fontsize=12)
    doc.save(p)
    doc.close()
    return p


@pytest.fixture(scope="session")
def tiny_mp4(tmp_path_factory) -> Path:
    """A 1-second 64x64 black video, built once per session."""
    import subprocess

    from polytool.core.ffmpeg import ffmpeg_path

    out = tmp_path_factory.mktemp("media") / "tiny.mp4"
    subprocess.run(
        [
            ffmpeg_path(),
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=64x64:d=1",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=mono:sample_rate=8000",
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(out),
        ],
        check=True,
    )
    return out

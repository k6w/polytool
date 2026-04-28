"""Tests for `pt pdf`."""

from __future__ import annotations

import pytest

pytest.importorskip("pypdf")
pytest.importorskip("pymupdf")
pytest.importorskip("pdfplumber")
pytest.importorskip("pikepdf")


def test_merge(runner, cli_app, tiny_pdf, tmp_path) -> None:
    out = tmp_path / "merged.pdf"
    result = runner.invoke(
        cli_app, ["pdf", "merge", str(tiny_pdf), str(tiny_pdf), "-o", str(out)]
    )
    assert result.exit_code == 0
    import pypdf

    reader = pypdf.PdfReader(str(out))
    # tiny_pdf has 2 pages; merging it twice = 4
    assert len(reader.pages) == 4


def test_merge_one_input(runner, cli_app, tiny_pdf, tmp_path) -> None:
    result = runner.invoke(
        cli_app, ["pdf", "merge", str(tiny_pdf), "-o", str(tmp_path / "m.pdf")]
    )
    assert result.exit_code != 0


def test_split_per_page(runner, cli_app, tiny_pdf, tmp_path) -> None:
    out_dir = tmp_path / "pages"
    result = runner.invoke(cli_app, ["pdf", "split", str(tiny_pdf), "-o", str(out_dir)])
    assert result.exit_code == 0
    files = sorted(out_dir.glob("*.pdf"))
    assert len(files) == 2  # tiny_pdf has 2 pages


def test_split_range(runner, cli_app, tiny_pdf, tmp_path) -> None:
    out = tmp_path / "p1.pdf"
    result = runner.invoke(
        cli_app, ["pdf", "split", str(tiny_pdf), "--pages", "1", "-o", str(out)]
    )
    assert result.exit_code == 0
    assert out.exists()


def test_compress(runner, cli_app, tiny_pdf, tmp_path) -> None:
    out = tmp_path / "small.pdf"
    result = runner.invoke(cli_app, ["pdf", "compress", str(tiny_pdf), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_extract_text(runner, cli_app, tiny_pdf) -> None:
    result = runner.invoke(cli_app, ["pdf", "extract-text", str(tiny_pdf)])
    assert result.exit_code == 0
    assert "hello world" in result.stdout.lower()


def test_to_images(runner, cli_app, tiny_pdf, tmp_path) -> None:
    out_dir = tmp_path / "imgs"
    result = runner.invoke(
        cli_app, ["pdf", "to-images", str(tiny_pdf), "-o", str(out_dir), "--dpi", "72"]
    )
    assert result.exit_code == 0
    pngs = list(out_dir.glob("*.png"))
    assert len(pngs) == 2


def test_from_images(runner, cli_app, tiny_jpg, tmp_path) -> None:
    out = tmp_path / "out.pdf"
    # Use the same image twice to produce a 2-page PDF
    result = runner.invoke(
        cli_app,
        ["pdf", "from-images", str(tiny_jpg), str(tiny_jpg), "-o", str(out)],
    )
    assert result.exit_code == 0
    import pypdf

    reader = pypdf.PdfReader(str(out))
    assert len(reader.pages) == 2


def test_missing_input(runner, cli_app, tmp_path) -> None:
    result = runner.invoke(
        cli_app, ["pdf", "extract-text", str(tmp_path / "nope.pdf")]
    )
    assert result.exit_code != 0

"""Tests for `pt file`."""

from __future__ import annotations

import zipfile
from pathlib import Path


def test_rename_dry_run(runner, cli_app, tmp_path) -> None:
    (tmp_path / "a.JPG").write_bytes(b"x")
    (tmp_path / "b.JPG").write_bytes(b"y")
    result = runner.invoke(
        cli_app,
        ["file", "rename", "*.JPG", "--to", "{name}.jpg", "--dir", str(tmp_path), "--dry-run"],
    )
    assert result.exit_code == 0
    # Files unchanged after dry run
    assert (tmp_path / "a.JPG").exists()
    assert (tmp_path / "b.JPG").exists()


def test_rename_actual(runner, cli_app, tmp_path) -> None:
    # Use names that differ by more than case so the test works on case-insensitive FS.
    (tmp_path / "img1.txt").write_bytes(b"x")
    (tmp_path / "img2.txt").write_bytes(b"y")
    result = runner.invoke(
        cli_app,
        [
            "file", "rename", "*.txt",
            "--to", "renamed_{n:02}.txt",
            "--dir", str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / "renamed_01.txt").exists()
    assert (tmp_path / "renamed_02.txt").exists()
    assert not (tmp_path / "img1.txt").exists()


def test_rename_no_match(runner, cli_app, tmp_path) -> None:
    result = runner.invoke(
        cli_app,
        ["file", "rename", "*.NOPE", "--to", "x", "--dir", str(tmp_path)],
    )
    assert result.exit_code != 0


def test_dedupe_finds_duplicates(runner, cli_app, tmp_path) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    c = tmp_path / "c.txt"
    a.write_bytes(b"same content")
    b.write_bytes(b"same content")
    c.write_bytes(b"unique")
    result = runner.invoke(cli_app, ["file", "dedupe", str(tmp_path)])
    assert result.exit_code == 0
    assert "duplicate" in result.stdout.lower()
    # Without --delete, both files still exist
    assert a.exists() and b.exists()


def test_dedupe_delete(runner, cli_app, tmp_path) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"same")
    b.write_bytes(b"same")
    result = runner.invoke(cli_app, ["file", "dedupe", str(tmp_path), "--delete"])
    assert result.exit_code == 0
    survivors = [p for p in (a, b) if p.exists()]
    assert len(survivors) == 1


def test_bigfiles(runner, cli_app, tmp_path) -> None:
    (tmp_path / "small.txt").write_bytes(b"x")
    (tmp_path / "big.bin").write_bytes(b"x" * 10_000)
    result = runner.invoke(cli_app, ["file", "bigfiles", str(tmp_path), "--top", "5"])
    assert result.exit_code == 0
    # Big file appears first
    lines = result.stdout.strip().splitlines()
    assert "big.bin" in lines[0]


def test_organize_by_extension(runner, cli_app, tmp_path) -> None:
    (tmp_path / "doc.pdf").write_bytes(b"x")
    (tmp_path / "img.jpg").write_bytes(b"x")
    (tmp_path / "img2.jpg").write_bytes(b"x")
    result = runner.invoke(cli_app, ["file", "organize", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "pdf" / "doc.pdf").exists()
    assert (tmp_path / "jpg" / "img.jpg").exists()


def test_archive_zip(runner, cli_app, tmp_path) -> None:
    src = tmp_path / "data"
    src.mkdir()
    (src / "a.txt").write_bytes(b"hello")
    (src / "b.txt").write_bytes(b"world")
    out = tmp_path / "out.zip"
    result = runner.invoke(cli_app, ["file", "archive", str(src), "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    with zipfile.ZipFile(out) as zf:
        names = {Path(n).name for n in zf.namelist()}
    assert {"a.txt", "b.txt"}.issubset(names)


def test_archive_targz(runner, cli_app, tmp_path) -> None:
    import tarfile

    src = tmp_path / "data"
    src.mkdir()
    (src / "a.txt").write_bytes(b"hi")
    out = tmp_path / "out.tar.gz"
    result = runner.invoke(cli_app, ["file", "archive", str(src), "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    with tarfile.open(out) as tf:
        names = {Path(n).name for n in tf.getnames()}
    assert "a.txt" in names


def test_archive_unsupported(runner, cli_app, tmp_path) -> None:
    src = tmp_path / "x.txt"
    src.write_bytes(b"x")
    out = tmp_path / "out.bogus"
    result = runner.invoke(cli_app, ["file", "archive", str(src), "--output", str(out)])
    assert result.exit_code != 0

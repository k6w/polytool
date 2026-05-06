"""File ops: rename, dedupe, bigfiles, organize, archive."""

from __future__ import annotations

import hashlib
import shutil
import tarfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Annotated

import typer

from polytool.core.console import console, err_console
from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="file",
    help="File ops (rename, dedupe, bigfiles, organize, archive).",
    no_args_is_help=True,
)


@app.command("rename")
def cmd_rename(
    pattern: Annotated[str, typer.Argument(help="Glob to match (e.g. '*.JPG').")],
    template: Annotated[
        str,
        typer.Option(
            "--to",
            help="New name template; placeholders: {name} {ext} {n} {n:03}.",
        ),
    ],
    directory: Annotated[
        Path,
        typer.Option("--dir", "-d", help="Directory to scan (default: cwd)"),
    ] = Path(),
    start: Annotated[int, typer.Option("--start", help="Starting counter")] = 1,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print only, don't rename")] = False,
) -> None:
    """Batch rename files matching a glob.

    Examples:

        pt file rename "*.JPG" --to "{name}.jpg"
        pt file rename "IMG_*.png" --to "photo_{n:03}.png"
    """
    files = sorted(directory.glob(pattern))
    if not files:
        raise PolytoolError(f"No files matched {pattern!r} in {directory}")

    n = start
    plans: list[tuple[Path, Path]] = []
    for src in files:
        new_name = template.format(name=src.stem, ext=src.suffix.lstrip("."), n=n)
        dst = src.with_name(new_name)
        plans.append((src, dst))
        n += 1

    for src, dst in plans:
        if dry_run:
            err_console.print(f"[dim]{src.name}[/dim] -> [bold]{dst.name}[/bold]")
            continue
        if dst.exists() and dst != src:
            raise PolytoolError(f"Target exists: {dst}")
        src.rename(dst)
    typer.echo(f"{'Would rename' if dry_run else 'Renamed'} {len(plans)} files.")


def _hash_file(path: Path, *, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while data := f.read(chunk):
            h.update(data)
    return h.hexdigest()


@app.command("dedupe")
def cmd_dedupe(
    directory: Annotated[Path, typer.Argument(help="Directory to scan")],
    delete: Annotated[
        bool, typer.Option("--delete", help="Actually delete duplicates (default: dry run)")
    ] = False,
    keep: Annotated[
        str,
        typer.Option("--keep", help="Which copy to keep: 'first' (oldest path) or 'shortest'"),
    ] = "first",
) -> None:
    """Find and (optionally) remove duplicate files (size-then-sha256).

    Examples:

        pt file dedupe ./Downloads
        pt file dedupe ./Downloads --delete
    """
    if not directory.is_dir():
        raise PolytoolError(f"Not a directory: {directory}")

    import contextlib

    by_size: dict[int, list[Path]] = defaultdict(list)
    for p in directory.rglob("*"):
        if p.is_file():
            by_size[p.stat().st_size].append(p)

    duplicates: list[list[Path]] = []
    for size, group in by_size.items():
        if size == 0 or len(group) < 2:
            continue
        by_hash: dict[str, list[Path]] = defaultdict(list)
        for p in group:
            with contextlib.suppress(OSError):
                by_hash[_hash_file(p)].append(p)
        for matches in by_hash.values():
            if len(matches) > 1:
                duplicates.append(matches)

    total_dupes = sum(len(g) - 1 for g in duplicates)
    if not duplicates:
        typer.echo("No duplicates found.")
        return

    saved_bytes = 0
    for group in duplicates:
        sorted_group = (
            sorted(group, key=lambda p: len(str(p))) if keep == "shortest" else sorted(group)
        )
        kept, victims = sorted_group[0], sorted_group[1:]
        for v in victims:
            saved_bytes += v.stat().st_size
            err_console.print(f"[red]dup[/red] {v}  [dim](keep {kept})[/dim]")
            if delete:
                v.unlink()
    verb = "Deleted" if delete else "Would delete"
    typer.echo(f"{verb} {total_dupes} duplicate file(s), reclaiming {saved_bytes:,} bytes.")


def _human_size(n: int) -> str:
    f = float(n)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if f < 1024:
            return f"{f:.1f} {unit}"
        f /= 1024
    return f"{f:.1f} PB"


@app.command("bigfiles")
def cmd_bigfiles(
    directory: Annotated[Path, typer.Argument(help="Directory to scan")] = Path(),
    top: Annotated[int, typer.Option("--top", "-n", help="How many to show")] = 20,
) -> None:
    """List the largest files under a directory.

    Examples:

        pt file bigfiles
        pt file bigfiles ~/Downloads --top 50
    """
    if not directory.is_dir():
        raise PolytoolError(f"Not a directory: {directory}")
    import contextlib

    sizes: list[tuple[int, Path]] = []
    for p in directory.rglob("*"):
        if p.is_file():
            with contextlib.suppress(OSError):
                sizes.append((p.stat().st_size, p))
    sizes.sort(key=lambda x: x[0], reverse=True)
    for size, path in sizes[:top]:
        typer.echo(f"{_human_size(size):>10}  {path}")


@app.command("organize")
def cmd_organize(
    directory: Annotated[Path, typer.Argument(help="Directory to organize")],
    by: Annotated[str, typer.Option("--by", help="'extension' or 'date'")] = "extension",
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print only")] = False,
) -> None:
    """Move files into subfolders by extension or modification date.

    Examples:

        pt file organize ~/Downloads
        pt file organize ~/Downloads --by date
    """
    if not directory.is_dir():
        raise PolytoolError(f"Not a directory: {directory}")
    if by not in {"extension", "date"}:
        raise PolytoolError(f"Unknown --by value {by!r}", hint="Use 'extension' or 'date'.")

    moved = 0
    for p in directory.iterdir():
        if not p.is_file():
            continue
        if by == "extension":
            sub = p.suffix.lstrip(".").lower() or "no-extension"
        else:
            from datetime import datetime

            d = datetime.fromtimestamp(p.stat().st_mtime)
            sub = f"{d.year:04}-{d.month:02}"
        target_dir = directory / sub
        target = target_dir / p.name
        if dry_run:
            err_console.print(f"[dim]{p.name}[/dim] -> [bold]{sub}/{p.name}[/bold]")
        else:
            target_dir.mkdir(exist_ok=True)
            shutil.move(str(p), str(target))
        moved += 1
    typer.echo(f"{'Would move' if dry_run else 'Moved'} {moved} file(s).")


@app.command("archive")
def cmd_archive(
    paths: Annotated[list[Path], typer.Argument(help="Files/folders to archive")],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output archive (.zip / .tar / .tar.gz / .tgz / .7z)",
        ),
    ],
) -> None:
    """Create an archive (zip / tar / tar.gz / 7z) from files and folders.

    Examples:

        pt file archive ./project --output project.zip
        pt file archive a.txt b.txt --output bundle.tar.gz
        pt file archive ./big_folder --output big.7z
    """
    if not paths:
        raise PolytoolError("No input paths given")
    out = output
    name = out.name.lower()

    def _walk(root: Path):
        if root.is_file():
            yield root, root.name
            return
        for p in root.rglob("*"):
            if p.is_file():
                yield p, str(p.relative_to(root.parent))

    if name.endswith(".zip"):
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for root in paths:
                for src, arcname in _walk(root):
                    zf.write(src, arcname)
    elif name.endswith((".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".tar")):
        mode = "w"
        if name.endswith((".tar.gz", ".tgz")):
            mode = "w:gz"
        elif name.endswith(".tar.bz2"):
            mode = "w:bz2"
        elif name.endswith(".tar.xz"):
            mode = "w:xz"
        with tarfile.open(out, mode) as tf:
            for root in paths:
                tf.add(root, arcname=root.name)
    elif name.endswith(".7z"):
        from polytool.core.lazy import require_extra

        py7zr = require_extra("py7zr", extra="archive")
        with py7zr.SevenZipFile(out, "w") as zf:
            for root in paths:
                zf.writeall(root, arcname=root.name)
    else:
        raise PolytoolError(
            f"Unsupported archive type {out.suffix!r}",
            hint="Use .zip, .tar(.gz/.bz2/.xz), .tgz, or .7z",
        )
    console.print(f"[green]Wrote[/green] {out}")

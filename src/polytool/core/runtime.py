"""Managed JavaScript runtime — Deno, downloaded on demand.

Some yt-dlp downloads (notably YouTube's "n-challenge") require an external
JS runtime to solve a piece of obfuscated JavaScript. Rather than make users
install Node/Deno system-wide, polytool can fetch a Deno binary into
``~/.polytool/runtime/`` and prepend that directory to ``PATH`` for yt-dlp's
subprocess lookups.

* Single binary, ~50-80 MB depending on platform.
* No admin rights needed — lives under the user's home dir.
* Removed cleanly via ``pt dl runtime clear``.
"""

from __future__ import annotations

import os
import platform
import shutil
import stat
import sys
import zipfile
from pathlib import Path

from polytool.core.console import err_console

RUNTIME_DIR: Path = Path.home() / ".polytool" / "runtime"

# We download from GitHub's "latest" redirect so the version follows upstream.
_DENO_LATEST_BASE = "https://github.com/denoland/deno/releases/latest/download"

# Names of system runtimes yt-dlp's EJS plugin will recognize on PATH.
_RECOGNIZED_RUNTIMES: tuple[str, ...] = ("deno", "node", "bun")


def _deno_archive_name() -> str:
    """Return the Deno release archive name for this platform/arch."""
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64", "x64"}:
        arch = "x86_64"
    elif machine in {"arm64", "aarch64"}:
        arch = "aarch64"
    else:
        raise RuntimeError(
            f"Unsupported CPU arch for managed Deno install: {machine!r}. "
            "Install Deno or Node manually."
        )

    if sys.platform == "win32":
        return f"deno-{arch}-pc-windows-msvc.zip"
    if sys.platform == "darwin":
        return f"deno-{arch}-apple-darwin.zip"
    if sys.platform.startswith("linux"):
        return f"deno-{arch}-unknown-linux-gnu.zip"
    raise RuntimeError(f"Unsupported platform for managed Deno install: {sys.platform!r}")


def deno_binary_path() -> Path:
    """Where the managed Deno binary lives on disk."""
    name = "deno.exe" if sys.platform == "win32" else "deno"
    return RUNTIME_DIR / name


def system_runtime_path() -> str | None:
    """Return the absolute path of any JS runtime already on the user's PATH."""
    for tool in _RECOGNIZED_RUNTIMES:
        found = shutil.which(tool)
        if found:
            return found
    return None


def is_managed_deno_installed() -> bool:
    """True iff polytool's own Deno binary exists and is runnable."""
    p = deno_binary_path()
    if not p.exists():
        return False
    if sys.platform == "win32":
        return True
    return bool(p.stat().st_mode & stat.S_IXUSR)


def install_deno() -> Path:
    """Download Deno into ``RUNTIME_DIR`` and return the path to the binary.

    Streams the zip with a Rich progress bar (this is a ~50-80 MB download).
    Overwrites any existing binary.
    """
    import httpx
    from rich.progress import (
        BarColumn,
        DownloadColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
    )

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    archive_name = _deno_archive_name()
    url = f"{_DENO_LATEST_BASE}/{archive_name}"
    archive_path = RUNTIME_DIR / archive_name

    err_console.print(f"[dim]downloading {archive_name}[/dim]")
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]Deno"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=err_console,
        transient=False,
    )

    with progress, httpx.stream("GET", url, follow_redirects=True, timeout=300) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length") or 0) or None
        task = progress.add_task("Deno", total=total)
        with archive_path.open("wb") as f:
            for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                f.write(chunk)
                progress.update(task, advance=len(chunk))

    err_console.print("[dim]extracting...[/dim]")
    with zipfile.ZipFile(archive_path) as zf:
        zf.extractall(RUNTIME_DIR)
    archive_path.unlink()

    binary = deno_binary_path()
    if not binary.exists():
        raise RuntimeError(f"Deno extracted but binary not found at {binary}")
    if sys.platform != "win32":
        binary.chmod(binary.stat().st_mode | 0o755)
    return binary


def ensure_runtime_in_path() -> str | None:
    """Make sure a JS runtime is reachable to subprocesses.

    Returns the absolute path of the runtime in use, or ``None`` if none is
    available. If the managed Deno is installed but its directory isn't on
    ``PATH`` yet, we prepend it (in-process only — no shell rc files touched).
    """
    sys_path = system_runtime_path()
    if sys_path:
        return sys_path
    if is_managed_deno_installed():
        binary = deno_binary_path()
        parent = str(binary.parent)
        current_path = os.environ.get("PATH", "")
        segments = current_path.split(os.pathsep)
        if parent not in segments:
            os.environ["PATH"] = parent + os.pathsep + current_path
        return str(binary)
    return None


def remove_runtime() -> None:
    """Delete the managed runtime directory."""
    if RUNTIME_DIR.exists():
        shutil.rmtree(RUNTIME_DIR)

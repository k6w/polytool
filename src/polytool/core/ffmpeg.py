"""ffmpeg locator — prefer system ffmpeg on PATH, fall back to imageio-ffmpeg."""

from __future__ import annotations

import shutil
from functools import cache

from polytool.core.lazy import try_import


@cache
def ffmpeg_path() -> str:
    """Return a usable ffmpeg binary path.

    Order:
    1. system ffmpeg on PATH (fast, no first-run download)
    2. imageio-ffmpeg's bundled binary (auto-downloads ~70 MB on first call)

    Raises PolytoolError if neither is available.
    """
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    iio = try_import("imageio_ffmpeg")
    if iio is not None:
        return iio.get_ffmpeg_exe()

    from polytool.core.errors import PolytoolError

    from rich.markup import escape

    raise PolytoolError(
        "ffmpeg not found.",
        hint="Install ffmpeg system-wide, or install the 'vid' extra: "
        f"[cyan]uv tool install '{escape('polytool[vid]')}'[/cyan]",
    )

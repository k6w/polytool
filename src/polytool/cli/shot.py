"""Screenshot utilities (screen capture via mss, web pages via Playwright)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer

from polytool.core.console import console
from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="shot",
    help="Screenshots (screen capture, web page).",
    no_args_is_help=True,
)


@app.command("screen")
def cmd_screen(
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output PNG (default: screen.png)"),
    ] = None,
    monitor: Annotated[
        int,
        typer.Option(
            "--monitor", "-m", help="Monitor index (0=all, 1=primary, ...)"
        ),
    ] = 0,
) -> None:
    """Capture the screen.

    Examples:

        pt shot screen
        pt shot screen --monitor 2 -o second-screen.png
    """
    from polytool.core.lazy import require_extra

    mss_mod = require_extra("mss", extra="shot")

    out = output or Path("screen.png")
    MSS = getattr(mss_mod, "MSS", None) or mss_mod.mss  # noqa: N806
    with MSS() as sct:
        if monitor < 0 or monitor >= len(sct.monitors):
            raise PolytoolError(
                f"Monitor index {monitor} out of range (0..{len(sct.monitors) - 1})",
            )
        mon = sct.monitors[monitor]
        sct_img = sct.grab(mon)
        mss_mod.tools.to_png(sct_img.rgb, sct_img.size, output=str(out))
    console.print(f"[green]Wrote[/green] {out}")


@app.command("web")
def cmd_web(
    url: Annotated[str, typer.Argument(help="URL to capture")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output PNG (default: page.png)"),
    ] = None,
    full_page: Annotated[
        bool,
        typer.Option("--full-page/--viewport", help="Capture full scroll height"),
    ] = True,
    width: Annotated[int, typer.Option("--width", help="Viewport width (px)")] = 1280,
    height: Annotated[int, typer.Option("--height", help="Viewport height (px)")] = 800,
    wait_ms: Annotated[
        int, typer.Option("--wait", help="Extra ms to wait after load")
    ] = 0,
) -> None:
    """Capture a screenshot of a web page (via Playwright Chromium).

    On first run you may need: [cyan]pt shot web --install[/cyan].

    Examples:

        pt shot web https://example.com
        pt shot web https://example.com --viewport --width 1920 --height 1080
    """
    from polytool.core.lazy import require_extra

    playwright = require_extra("playwright.sync_api", extra="shot")

    out = output or Path("page.png")
    try:
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": width, "height": height})
            page = ctx.new_page()
            page.goto(url, wait_until="networkidle")
            if wait_ms > 0:
                page.wait_for_timeout(wait_ms)
            page.screenshot(path=str(out), full_page=full_page)
            browser.close()
    except Exception as exc:
        msg = str(exc).lower()
        if "executable doesn't exist" in msg or "missing dependencies" in msg or "browsertype" in msg:
            raise PolytoolError(
                "Playwright Chromium not installed.",
                hint="Run: [cyan]pt shot install[/cyan]",
            ) from exc
        raise PolytoolError(f"Web capture failed: {exc}") from exc
    console.print(f"[green]Wrote[/green] {out}")


@app.command("install")
def cmd_install() -> None:
    """Install the Chromium browser used by `pt shot web`.

    Examples:

        pt shot install
    """
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except FileNotFoundError as exc:
        raise PolytoolError(
            "Playwright not found.",
            hint="Install: [cyan]uv tool install 'polytool[shot]'[/cyan]",
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise PolytoolError(f"playwright install failed (exit {exc.returncode})") from exc
    console.print("[green]Installed Chromium.[/green]")

"""Image utilities — convert, resize, compress, EXIF, palette, watermark, ASCII, bg-remove, OCR."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from polytool.core.console import console, err_console
from polytool.core.errors import PolytoolError
from polytool.core.io import default_output

app = typer.Typer(
    name="img",
    help="Image utilities (convert, resize, bg-remove, OCR, ...).",
    no_args_is_help=True,
)


def _open_image(source: Path):
    """Open an image, handling HEIC/AVIF/SVG via plugins/resvg."""
    from polytool.core.lazy import require_extra

    PIL_Image = require_extra("PIL.Image", extra="img")

    suffix = source.suffix.lower()
    if suffix == ".svg":
        resvg_py = require_extra("resvg_py", extra="img")
        png_bytes = resvg_py.svg_to_bytes(svg_path=str(source))
        from io import BytesIO

        return PIL_Image.open(BytesIO(bytes(png_bytes)))

    # HEIC/AVIF plugins register themselves on import.
    if suffix in {".heic", ".heif"}:
        try:
            import pillow_heif  # type: ignore

            pillow_heif.register_heif_opener()
        except ImportError as exc:
            raise PolytoolError(
                "HEIC support missing.",
                hint="Install: [cyan]uv tool install 'polytool[img]'[/cyan]",
            ) from exc
    if suffix == ".avif":
        try:
            import pillow_avif  # noqa: F401  # type: ignore
        except ImportError as exc:
            raise PolytoolError(
                "AVIF support missing.",
                hint="Install: [cyan]uv tool install 'polytool[img]'[/cyan]",
            ) from exc

    try:
        return PIL_Image.open(source)
    except FileNotFoundError as exc:
        raise PolytoolError(f"File not found: {source}") from exc
    except Exception as exc:
        raise PolytoolError(f"Could not open image: {exc}") from exc


@app.command("convert")
def cmd_convert(
    source: Annotated[Path, typer.Argument(help="Input image (any common format)")],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file (extension picks format). Default: same name, target ext.",
        ),
    ] = None,
    to: Annotated[
        str | None,
        typer.Option("--to", "-t", help="Target format (png, jpg, webp, avif, ...)"),
    ] = None,
    quality: Annotated[int, typer.Option("--quality", "-q", help="JPEG/WEBP quality 1-100")] = 90,
) -> None:
    """Convert images between formats (png, jpg, webp, avif, heic, gif, bmp, tiff, svg→raster).

    Examples:

        pt img convert photo.heic -o photo.jpg
        pt img convert logo.svg --to png
        pt img convert pic.png --to webp -q 80
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    if output is None:
        if to is None:
            raise PolytoolError("Provide --output or --to.")
        output = default_output(source, "." + to.lstrip("."))
    fmt_ext = to or output.suffix.lstrip(".")
    img = _open_image(source)

    save_kwargs: dict = {}
    fmt_lower = fmt_ext.lower()
    pil_format = {"jpg": "JPEG", "jpeg": "JPEG", "tif": "TIFF"}.get(fmt_lower, fmt_lower.upper())

    if pil_format in {"JPEG", "WEBP"}:
        save_kwargs["quality"] = quality
        if img.mode in {"RGBA", "P", "LA"} and pil_format == "JPEG":
            from PIL import Image

            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
            img = bg
    if pil_format == "PNG":
        save_kwargs["optimize"] = True

    try:
        img.save(
            output, format=pil_format if pil_format != fmt_lower.upper() else None, **save_kwargs
        )
    except Exception as exc:
        raise PolytoolError(f"Could not save as {pil_format}: {exc}") from exc
    console.print(f"[green]Wrote[/green] {output}")


@app.command("resize")
def cmd_resize(
    source: Annotated[Path, typer.Argument(help="Input image")],
    width: Annotated[int | None, typer.Option("--width", "-w", help="Target width (px)")] = None,
    height: Annotated[int | None, typer.Option("--height", "-h", help="Target height (px)")] = None,
    percent: Annotated[
        float | None, typer.Option("--percent", "-p", help="Scale by N percent")
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output (default: <name>_resized.<ext>)"),
    ] = None,
) -> None:
    """Resize an image. Provide --width and/or --height, or --percent.

    Examples:

        pt img resize big.jpg --width 800
        pt img resize big.jpg --width 800 --height 600
        pt img resize big.jpg --percent 50
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    img = _open_image(source)
    w0, h0 = img.size

    if percent is not None:
        if percent <= 0:
            raise PolytoolError("--percent must be > 0")
        new_w = int(w0 * percent / 100)
        new_h = int(h0 * percent / 100)
    elif width and height:
        new_w, new_h = width, height
    elif width:
        new_w = width
        new_h = int(h0 * (width / w0))
    elif height:
        new_h = height
        new_w = int(w0 * (height / h0))
    else:
        raise PolytoolError("Provide --width, --height, or --percent.")

    from PIL import Image as _PIL

    resized = img.resize((new_w, new_h), _PIL.Resampling.LANCZOS)
    out = output or source.with_stem(source.stem + "_resized")
    resized.save(out)
    console.print(f"[green]Wrote[/green] {out} ({new_w}x{new_h})")


@app.command("compress")
def cmd_compress(
    source: Annotated[Path, typer.Argument(help="Input image (jpg/png/webp)")],
    quality: Annotated[int, typer.Option("--quality", "-q", help="1-100")] = 70,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output (default: <name>_compressed.<ext>)"),
    ] = None,
) -> None:
    """Recompress an image at lower quality / better optimization.

    Examples:

        pt img compress big.jpg -q 60
        pt img compress photo.png   # PNG optimize pass
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    img = _open_image(source)
    out = output or source.with_stem(source.stem + "_compressed")
    suffix = out.suffix.lower()
    save_kwargs: dict = {}
    if suffix in {".jpg", ".jpeg", ".webp"}:
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
    elif suffix == ".png":
        save_kwargs["optimize"] = True
    img.save(out, **save_kwargs)
    before = source.stat().st_size
    after = out.stat().st_size
    console.print(
        f"[green]Wrote[/green] {out} ({before:,} -> {after:,} bytes, {(after / before) * 100:.0f}%)"
    )


@app.command("exif")
def cmd_exif(
    source: Annotated[Path, typer.Argument(help="JPEG/TIFF input")],
    strip: Annotated[
        bool,
        typer.Option("--strip", help="Remove all EXIF and write to <name>_clean.<ext>"),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output for --strip (default: <name>_clean.<ext>)"),
    ] = None,
) -> None:
    """View or strip EXIF metadata.

    Examples:

        pt img exif photo.jpg
        pt img exif photo.jpg --strip
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    if not strip:
        from PIL import ExifTags, Image

        img = Image.open(source)
        exif = img.getexif()
        if not exif:
            console.print("[dim]No EXIF data.[/dim]")
            return
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            console.print(f"[cyan]{tag}[/cyan] = {value}")
        return

    out = output or source.with_stem(source.stem + "_clean")
    try:
        import piexif

        piexif.remove(str(source), str(out))
    except Exception:
        # Fallback: re-encode without EXIF via Pillow
        from PIL import Image

        img = Image.open(source)
        data = list(img.getdata())
        clean = Image.new(img.mode, img.size)
        clean.putdata(data)
        clean.save(out)
    console.print(f"[green]Stripped[/green] EXIF -> {out}")


@app.command("palette")
def cmd_palette(
    source: Annotated[Path, typer.Argument(help="Image to extract palette from")],
    count: Annotated[int, typer.Option("--count", "-n", help="How many colors")] = 6,
) -> None:
    """Extract dominant colors from an image.

    Examples:

        pt img palette photo.jpg
        pt img palette photo.jpg --count 10
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    from polytool.core.lazy import require_extra

    ct = require_extra("colorthief", extra="img")
    thief = ct.ColorThief(str(source))
    if count == 1:
        colors = [thief.get_color(quality=1)]
    else:
        colors = thief.get_palette(color_count=max(count, 2), quality=1)[:count]
    for r, g, b in colors:
        hex_ = f"#{r:02x}{g:02x}{b:02x}"
        console.print(f"[on rgb({r},{g},{b})]    [/on rgb({r},{g},{b})]  {hex_}  rgb({r},{g},{b})")


@app.command("watermark")
def cmd_watermark(
    source: Annotated[Path, typer.Argument(help="Image to watermark")],
    text: Annotated[str, typer.Option("--text", help="Watermark text")] = "© polytool",
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Output (default: <name>_wm.<ext>)")
    ] = None,
    opacity: Annotated[float, typer.Option("--opacity", help="0.0-1.0")] = 0.4,
    position: Annotated[
        str,
        typer.Option(
            "--position",
            help="topleft | topright | bottomleft | bottomright | center",
        ),
    ] = "bottomright",
    size: Annotated[int, typer.Option("--size", help="Font size (px)")] = 48,
) -> None:
    """Overlay text watermark on an image.

    Examples:

        pt img watermark photo.jpg --text "© 2026"
        pt img watermark photo.jpg --position center --opacity 0.6
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    from PIL import Image, ImageDraw, ImageFont

    img = _open_image(source).convert("RGBA")
    w, h = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype("arial.ttf", size)
    except OSError:
        font = ImageFont.load_default(size)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = max(20, size // 2)
    positions = {
        "topleft": (pad, pad),
        "topright": (w - tw - pad, pad),
        "bottomleft": (pad, h - th - pad),
        "bottomright": (w - tw - pad, h - th - pad),
        "center": ((w - tw) // 2, (h - th) // 2),
    }
    if position not in positions:
        raise PolytoolError(
            f"Unknown position {position!r}",
            hint=f"One of: {', '.join(positions)}",
        )
    x, y = positions[position]
    alpha = int(255 * max(0.0, min(1.0, opacity)))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha))
    out_img = Image.alpha_composite(img, overlay)

    out = output or source.with_stem(source.stem + "_wm")
    if out.suffix.lower() in {".jpg", ".jpeg"}:
        out_img = out_img.convert("RGB")
    out_img.save(out)
    console.print(f"[green]Wrote[/green] {out}")


@app.command("ascii")
def cmd_ascii(
    source: Annotated[Path, typer.Argument(help="Image to render as ASCII")],
    width: Annotated[int, typer.Option("--width", "-w", help="ASCII art width (chars)")] = 100,
) -> None:
    """Render an image as ASCII art.

    Examples:

        pt img ascii photo.jpg
        pt img ascii photo.jpg --width 60
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    from polytool.core.lazy import require_extra

    am = require_extra("ascii_magic", extra="img")
    art = am.AsciiArt.from_image(str(source))
    art.to_terminal(columns=width)


@app.command("bg-remove")
def cmd_bg_remove(
    source: Annotated[Path, typer.Argument(help="Image to remove background from")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output PNG (default: <name>_nobg.png)"),
    ] = None,
) -> None:
    """Remove the background of an image (transparent PNG).

    On first run, downloads a ~170 MB U2-Net model to ~/.u2net/.

    Examples:

        pt img bg-remove portrait.jpg
        pt img bg-remove product.png -o product_cutout.png
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    from polytool.core.lazy import require_extra

    rembg = require_extra("rembg", extra="ai")

    err_console.print("[dim]Removing background (first run downloads ~170 MB model)...[/dim]")
    data = source.read_bytes()
    out_bytes = rembg.remove(data)
    out = output or source.with_stem(source.stem + "_nobg").with_suffix(".png")
    out.write_bytes(out_bytes)
    console.print(f"[green]Wrote[/green] {out}")


@app.command("ocr")
def cmd_ocr(
    source: Annotated[Path, typer.Argument(help="Image with text")],
    engine: Annotated[
        str,
        typer.Option("--engine", help="'tesseract' (small, needs system tesseract) or 'easyocr'"),
    ] = "tesseract",
    lang: Annotated[str, typer.Option("--lang", help="Language code")] = "eng",
) -> None:
    """Extract text from an image using OCR.

    Examples:

        pt img ocr scan.jpg
        pt img ocr scan.jpg --engine easyocr --lang en
    """
    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    from polytool.core.lazy import require_extra

    if engine == "tesseract":
        pytesseract = require_extra("pytesseract", extra="ocr")
        PIL_Image = require_extra("PIL.Image", extra="img")

        try:
            text = pytesseract.image_to_string(PIL_Image.open(source), lang=lang)
        except pytesseract.TesseractNotFoundError as exc:
            raise PolytoolError(
                "Tesseract binary not found.",
                hint="Install Tesseract system-wide, or use --engine easyocr.",
            ) from exc
        typer.echo(text)
    elif engine == "easyocr":
        easyocr = require_extra("easyocr", extra="ocr")
        reader = easyocr.Reader([lang.replace("eng", "en")])
        results = reader.readtext(str(source), detail=0)
        for line in results:
            typer.echo(line)
    else:
        raise PolytoolError(f"Unknown engine {engine!r}", hint="Use 'tesseract' or 'easyocr'.")

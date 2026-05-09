# Architecture

Internal map of polytool — how the package is laid out, how lazy imports work, what the error/IO model looks like, and how to add a new verb.

## Package layout

```
src/polytool/
├── __init__.py          # __version__
├── __main__.py          # `python -m polytool`
├── cli/
│   ├── __init__.py      # Root Typer app, registers all 16 sub-apps
│   ├── img.py vid.py pdf.py dl.py data.py enc.py
│   ├── qr.py  gen.py  file.py net.py clip.py shot.py
│   └── color.py convert.py text.py cron.py
└── core/
    ├── io.py            # path/stdin & path/stdout helpers
    ├── progress.py      # Rich Progress factory
    ├── lazy.py          # require_extra(), try_import()
    ├── errors.py        # PolytoolError, MissingExtraError, install_excepthook
    ├── console.py       # shared Rich Console (stderr for status)
    └── ffmpeg.py        # ffmpeg path resolver (system → bundled)
```

Each `cli/<group>.py` exposes a `app = typer.Typer(...)` and one function per verb. The root `cli/__init__.py` `add_typer`s all 16.

## Lazy imports — the single biggest UX lever

`pt --help` must stay snappy (≤ 100 ms cold). Heavy deps like Pillow, ffmpeg-python, rembg, easyocr, Playwright, pandas would blow that out instantly if imported at module top.

Two layers of discipline:

1. **Subcommand modules** restrict their *top-level* imports to: `typer`, `rich`, stdlib, `polytool.core.*`. No Pillow, no rembg, no PyMuPDF at the top.

2. **Verb bodies** call `require_extra("pillow", extra="img")` or `require_extra("rembg", extra="ai")` *inside* the function. The import only runs when the verb actually executes.

The wrapper in `core/lazy.py`:

```python
def require_extra(module: str, extra: str) -> ModuleType:
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise MissingExtraError(module, extra) from exc
```

When a user runs `pt img bg-remove` without the `[ai]` extra, they see:

```
Missing optional dependency: 'rembg' (from the 'ai' extra).
Hint: Install with: uv tool install 'polytool[ai]'
       Or for everything: uv tool install 'polytool[full]'
```

## Error model

Every user-facing error funnels through `core/errors.py`:

```python
class PolytoolError(Exception):
    def __init__(self, message: str, hint: str | None = None): ...
```

- Raise `PolytoolError("File not found: ...", hint="Try 'pt img convert ...'.")`
- The excepthook installed at root-CLI import time catches the exception, renders a red panel via Rich (with a cyan hint), and exits with code 1.
- This is what every `Errors:` section in the per-verb docs is referring to.

`MissingExtraError(PolytoolError)` is a specialization for "you need an extra" — same UX, but the message is generated automatically from `(module, extra)`.

## I/O model

Every verb that takes a file accepts:
- a path argument, or
- `-` (stdin), or
- omission (also stdin), where it makes semantic sense.

Helpers in `core/io.py`:
- `read_text(source)` / `read_bytes(source)` — read from path or stdin.
- `write_text(target, data)` / `write_bytes(target, data)` — write to path or stdout (`-`).
- `default_output(input_path, suffix)` — suggest `<name>.<suffix>` next to the input.

Verbs default `--output` to:
- next to the source for binary outputs (e.g. `<name>_resized.<ext>`)
- stdout for text outputs

so commands compose cleanly with `|` and `>`.

## Console split: stdout vs stderr

`core/console.py` exposes two Rich consoles:

- `console` — stdout. Use it for output the user might want to pipe (status lines that are part of the result).
- `err_console` — stderr. Use it for progress bars, debug-style status, and "doing X..." lines that shouldn't pollute pipelines.

Errors go to stderr automatically through the excepthook.

## ffmpeg resolution

`core/ffmpeg.py` resolves the binary path:

1. `shutil.which("ffmpeg")` — system install on PATH.
2. `imageio_ffmpeg.get_ffmpeg_exe()` — bundled binary; auto-downloads ~70 MB on first call.
3. Otherwise raises `PolytoolError` with the install hint.

Result is `@cache`-d so the lookup happens once per process.

## CLI framework: Typer

We use [Typer](https://typer.tiangolo.com/) (Click underneath) because:
- Type hints drive argument inference (`Annotated[Path, typer.Argument(...)]`).
- Rich-rendered `--help` with no extra setup.
- `--help` is consistent and discoverable for 16 groups × ~2-9 verbs each.
- `CliRunner` makes testing trivial (`tests/conftest.py` exposes a `runner` fixture).

## How to add a new verb

1. Decide which group (`pt <group> <verb>`) it belongs to. If a brand-new group, create `src/polytool/cli/<group>.py` with `app = typer.Typer(...)` at the top.
2. Add `@app.command("verb-name")` with a `def cmd_<verb>(...)` body.
3. **Top-level imports**: typer, rich, stdlib, `polytool.core.*` only. Heavy deps go inside the body via `require_extra`.
4. Always include an `Examples:` block in the docstring — it's shown in `--help`.
5. Errors: raise `PolytoolError(msg, hint=...)`. Don't `print(...)` and `sys.exit(1)`.
6. If a new group, register in `src/polytool/cli/__init__.py` (`from polytool.cli import <group>` + `app.add_typer(<group>.app, name="<group>")`).
7. Add tests in `tests/cli/test_<group>.py` — at least one happy-path and one error-path test using the `runner` fixture.
8. Add docs in `docs/<group>.md` (or extend an existing page).
9. Conventional commit (`feat(<group>): <verb>`).

## Testing strategy

- `tests/conftest.py` supplies a `runner` (Typer's `CliRunner`), tiny image / PDF / mp4 fixtures.
- Each `tests/cli/test_<group>.py` uses `runner.invoke(cli_app, [...])` and asserts on `result.exit_code` + `result.stdout`.
- Tests that need the network mock httpx (`net http`, `net ip-info`) or yt-dlp (`dl get`).
- ffmpeg tests use a real 1-second mp4 fixture with bundled ffmpeg — fast and integration-grade.
- Heavy tests (`shot screen` on headless Linux, `clip` without xclip) skip via `pytest.importorskip` / explicit skipif.
- We don't unit-test third-party libraries — only our argument plumbing, output paths, and error formatting.

## Performance budget

- `pt --help` cold start: < 100 ms (test in `tests/test_root.py`).
- `pt <group> --help`: < 120 ms.
- Heavy verbs can take their time once invoked.

If a regression slips in, `tests/test_root.py::test_help_is_fast` catches it in CI.

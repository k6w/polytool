"""Smoke tests for the root CLI."""

from __future__ import annotations

import time

from polytool import __version__


def test_help_runs(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["--help"])
    assert result.exit_code == 0
    assert "polytool" in result.stdout


def test_version_flag(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_is_fast() -> None:
    """The cold-import path must stay snappy.

    Budget: importing the root CLI module + invoking --help should complete in
    well under a second on any reasonable machine. Heavy deps must be lazy-loaded
    inside subcommand bodies, never at module top.
    """
    start = time.perf_counter()
    from polytool.cli import app  # noqa: F401  (deliberate import in test body)

    elapsed = time.perf_counter() - start
    # Generous budget for CI; real cold start should be < 0.2s.
    assert elapsed < 1.5, f"polytool.cli import took {elapsed:.2f}s (budget 1.5s)"

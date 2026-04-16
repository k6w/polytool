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

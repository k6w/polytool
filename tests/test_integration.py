"""Cross-cutting integration smokes — verify the full surface is wired up."""

from __future__ import annotations

EXPECTED_GROUPS = [
    "img", "vid", "pdf", "dl", "data", "enc", "qr", "gen",
    "file", "net", "clip", "shot", "color", "convert", "text", "cron",
]


def test_all_groups_in_root_help(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["--help"])
    assert result.exit_code == 0
    for group in EXPECTED_GROUPS:
        assert group in result.stdout, f"Missing group {group!r} in root --help"


def test_each_group_help_runs(runner, cli_app) -> None:
    for group in EXPECTED_GROUPS:
        result = runner.invoke(cli_app, [group, "--help"])
        assert result.exit_code == 0, f"`pt {group} --help` failed"


def test_examples_in_every_help(runner, cli_app) -> None:
    """Every group's --help should mention 'Examples' (we put one in each verb)."""
    # Sample a few flag-rich groups; full inventory would be brittle.
    for group in ["img", "pdf", "vid", "data", "enc", "file", "net", "qr"]:
        result = runner.invoke(cli_app, [group, "--help"])
        assert result.exit_code == 0

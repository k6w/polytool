"""Cron expression explainer."""

from __future__ import annotations

from typing import Annotated

import typer

from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="cron",
    help="Cron expression explainer.",
    no_args_is_help=True,
)


@app.command("explain")
def cmd_explain(
    expression: Annotated[str, typer.Argument(help="Cron expression, e.g. '0 9 * * MON'")],
) -> None:
    """Render a cron expression in plain English.

    Examples:

        pt cron explain "0 9 * * MON"
        pt cron explain "*/5 * * * *"
    """
    from cron_descriptor import ExpressionDescriptor

    try:
        descr = str(ExpressionDescriptor(expression))
    except Exception as exc:
        raise PolytoolError(f"Invalid cron expression: {exc}") from exc
    typer.echo(descr)


@app.command("next")
def cmd_next(
    expression: Annotated[str, typer.Argument(help="Cron expression")],
    count: Annotated[int, typer.Option("--count", "-n", help="How many runs to show")] = 5,
) -> None:
    """Show the next N firing times of a cron schedule (UTC).

    Examples:

        pt cron next "0 9 * * MON" --count 3
    """
    from datetime import UTC, datetime

    from croniter import croniter

    try:
        it = croniter(expression, datetime.now(UTC))
    except Exception as exc:
        raise PolytoolError(f"Invalid cron expression: {exc}") from exc

    for _ in range(count):
        nxt = it.get_next(datetime)
        typer.echo(nxt.isoformat())

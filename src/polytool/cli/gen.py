"""Generators (password, UUID, lorem ipsum)."""

from __future__ import annotations

import secrets
import string
import uuid as _uuid
from typing import Annotated

import typer

from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="gen",
    help="Generators (password, uuid, lorem ipsum).",
    no_args_is_help=True,
)


@app.command("password")
def cmd_password(
    length: Annotated[int, typer.Option("--length", "-n", help="Password length")] = 24,
    count: Annotated[int, typer.Option("--count", "-c", help="How many to generate")] = 1,
    no_symbols: Annotated[
        bool, typer.Option("--no-symbols", help="Letters and digits only")
    ] = False,
) -> None:
    """Generate cryptographically strong passwords.

    Examples:

        pt gen password --length 32
        pt gen password --count 5 --no-symbols
    """
    if length < 4:
        raise PolytoolError("--length must be at least 4")
    alphabet = string.ascii_letters + string.digits
    if not no_symbols:
        alphabet += "!@#$%^&*()-_=+[]{};:,.?"
    for _ in range(count):
        typer.echo("".join(secrets.choice(alphabet) for _ in range(length)))


@app.command("uuid")
def cmd_uuid(
    version: Annotated[
        str, typer.Argument(help="UUID version: v1, v3, v4 (random), v5, v7 (time-sortable)")
    ] = "v4",
    count: Annotated[int, typer.Option("--count", "-c", help="How many to generate")] = 1,
    namespace: Annotated[
        str | None,
        typer.Option("--namespace", help="Namespace UUID for v3/v5 (e.g. dns, url, oid, x500)"),
    ] = None,
    name: Annotated[str | None, typer.Option("--name", help="Name for v3/v5")] = None,
) -> None:
    """Generate UUIDs (v1/v3/v4/v5/v7).

    Examples:

        pt gen uuid v4
        pt gen uuid v7 --count 3
        pt gen uuid v5 --namespace dns --name example.com
    """
    v = version.lower().lstrip("v")
    namespaces = {
        "dns": _uuid.NAMESPACE_DNS,
        "url": _uuid.NAMESPACE_URL,
        "oid": _uuid.NAMESPACE_OID,
        "x500": _uuid.NAMESPACE_X500,
    }
    for _ in range(count):
        if v == "1":
            typer.echo(str(_uuid.uuid1()))
        elif v == "4":
            typer.echo(str(_uuid.uuid4()))
        elif v == "7":
            # Python 3.13 added uuid.uuid7
            uuid7 = getattr(_uuid, "uuid7", None)
            if uuid7 is not None:
                typer.echo(str(uuid7()))
            else:
                # Manual v7 fallback (won't be hit on 3.13+, but defensive)
                import os
                import time

                ts_ms = int(time.time() * 1000)
                rand_a = secrets.randbits(12)
                rand_b = secrets.randbits(62)
                ts_hi = (ts_ms >> 16) & 0xFFFFFFFF
                ts_lo = ts_ms & 0xFFFF
                bits = (
                    (ts_hi << 96)
                    | (ts_lo << 80)
                    | (0x7 << 76)
                    | (rand_a << 64)
                    | (0b10 << 62)
                    | rand_b
                )
                typer.echo(str(_uuid.UUID(int=bits)))
                _ = os
        elif v in {"3", "5"}:
            if not namespace or not name:
                raise PolytoolError(
                    f"v{v} requires --namespace and --name",
                    hint="Try: --namespace dns --name example.com",
                )
            ns = namespaces.get(namespace.lower())
            if ns is None:
                raise PolytoolError(
                    f"Unknown namespace {namespace!r}",
                    hint="One of: dns, url, oid, x500",
                )
            ctor = _uuid.uuid3 if v == "3" else _uuid.uuid5
            typer.echo(str(ctor(ns, name)))
        else:
            raise PolytoolError(
                f"Unsupported UUID version {version!r}",
                hint="One of: v1, v3, v4, v5, v7",
            )


@app.command("lorem")
def cmd_lorem(
    paragraphs: Annotated[int, typer.Option("--paragraphs", "-p", help="Number of paragraphs")] = 1,
    sentences: Annotated[
        int | None,
        typer.Option("--sentences", "-s", help="Sentences per paragraph (default: random)"),
    ] = None,
    words: Annotated[
        int | None, typer.Option("--words", "-w", help="Generate N words instead of paragraphs")
    ] = None,
    locale: Annotated[
        str, typer.Option("--locale", help="Locale (en_US, fr_FR, ja_JP, ...)")
    ] = "en_US",
) -> None:
    """Generate lorem ipsum / fake text.

    Examples:

        pt gen lorem
        pt gen lorem --paragraphs 3
        pt gen lorem --words 50
        pt gen lorem --locale fr_FR
    """
    from faker import Faker

    fake = Faker(locale)

    if words is not None:
        if words < 1:
            raise PolytoolError("--words must be >= 1")
        typer.echo(" ".join(fake.words(nb=words)))
        return

    if paragraphs < 1:
        raise PolytoolError("--paragraphs must be >= 1")
    chunks: list[str] = []
    for _ in range(paragraphs):
        if sentences is None:
            chunks.append(fake.paragraph(nb_sentences=5, variable_nb_sentences=True))
        else:
            chunks.append(fake.paragraph(nb_sentences=sentences, variable_nb_sentences=False))
    typer.echo("\n\n".join(chunks))

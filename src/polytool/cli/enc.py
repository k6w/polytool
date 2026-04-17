"""Hashing and encoding utilities (sha*, base64, url, html, jwt)."""

from __future__ import annotations

import base64 as _base64
import hashlib
import html as _html
import urllib.parse
from pathlib import Path
from typing import Annotated

import typer

from polytool.core.console import console
from polytool.core.errors import PolytoolError
from polytool.core.io import read_bytes, read_text

app = typer.Typer(
    name="enc",
    help="Hashing and encoding (sha256, base64, url, html, jwt).",
    no_args_is_help=True,
)

ALGORITHMS = ("md5", "sha1", "sha256", "sha512", "blake2b", "xxhash")


@app.command("hash")
def cmd_hash(
    algorithm: Annotated[
        str, typer.Argument(help=f"One of: {', '.join(ALGORITHMS)}")
    ],
    source: Annotated[
        Path | None,
        typer.Argument(help="File path. Use '-' or omit to read from stdin."),
    ] = None,
) -> None:
    """Compute a cryptographic or fast hash of FILE.

    Examples:

        pt enc hash sha256 README.md
        echo -n "hello" | pt enc hash sha256
        pt enc hash xxhash big.iso
    """
    algo = algorithm.lower()
    data = read_bytes(source)
    if algo == "xxhash":
        from polytool.core.lazy import require_extra

        xxh = require_extra("xxhash", extra="(builtin)")  # base dep
        digest = xxh.xxh3_64_hexdigest(data)
    elif algo in {"md5", "sha1", "sha256", "sha512", "blake2b"}:
        h = hashlib.new(algo)
        h.update(data)
        digest = h.hexdigest()
    else:
        raise PolytoolError(
            f"Unknown algorithm: {algorithm!r}",
            hint=f"Pick one of: {', '.join(ALGORITHMS)}",
        )
    typer.echo(digest)


@app.command("base64")
def cmd_base64(
    mode: Annotated[str, typer.Argument(help="'encode' or 'decode'")],
    source: Annotated[
        Path | None,
        typer.Argument(help="File or '-' for stdin"),
    ] = None,
    urlsafe: Annotated[
        bool,
        typer.Option("--urlsafe/--standard", help="Use URL-safe alphabet"),
    ] = False,
) -> None:
    """Base64 encode or decode data.

    Examples:

        pt enc base64 encode README.md
        echo -n "hello" | pt enc base64 encode
        pt enc base64 decode encoded.txt
    """
    if mode == "encode":
        data = read_bytes(source)
        if urlsafe:
            out = _base64.urlsafe_b64encode(data).decode("ascii")
        else:
            out = _base64.b64encode(data).decode("ascii")
        typer.echo(out)
    elif mode == "decode":
        text = read_text(source).strip()
        try:
            if urlsafe:
                raw = _base64.urlsafe_b64decode(text)
            else:
                raw = _base64.b64decode(text)
        except Exception as exc:
            raise PolytoolError(
                f"Invalid base64 input: {exc}",
                hint="Pass --urlsafe if the input was URL-encoded.",
            ) from exc
        try:
            typer.echo(raw.decode("utf-8"))
        except UnicodeDecodeError:
            import sys

            sys.stdout.buffer.write(raw)
    else:
        raise PolytoolError(f"mode must be 'encode' or 'decode', got {mode!r}")


@app.command("url")
def cmd_url(
    mode: Annotated[str, typer.Argument(help="'encode' or 'decode'")],
    text: Annotated[str | None, typer.Argument(help="Text (or omit for stdin)")] = None,
) -> None:
    """URL-encode or decode a string.

    Examples:

        pt enc url encode "hello world & friends"
        pt enc url decode "hello%20world%20%26%20friends"
    """
    payload = text if text is not None else read_text(None).rstrip("\n")
    if mode == "encode":
        typer.echo(urllib.parse.quote(payload, safe=""))
    elif mode == "decode":
        typer.echo(urllib.parse.unquote(payload))
    else:
        raise PolytoolError(f"mode must be 'encode' or 'decode', got {mode!r}")


@app.command("html")
def cmd_html(
    mode: Annotated[str, typer.Argument(help="'encode' or 'decode'")],
    text: Annotated[str | None, typer.Argument(help="Text (or omit for stdin)")] = None,
) -> None:
    """HTML-escape or unescape a string.

    Examples:

        pt enc html encode "<script>alert(1)</script>"
        pt enc html decode "&lt;b&gt;hi&lt;/b&gt;"
    """
    payload = text if text is not None else read_text(None).rstrip("\n")
    if mode == "encode":
        typer.echo(_html.escape(payload))
    elif mode == "decode":
        typer.echo(_html.unescape(payload))
    else:
        raise PolytoolError(f"mode must be 'encode' or 'decode', got {mode!r}")


@app.command("jwt-decode")
def cmd_jwt_decode(
    token: Annotated[str, typer.Argument(help="JWT to decode (header.payload.signature)")],
) -> None:
    """Decode a JWT WITHOUT signature verification (header + payload only).

    Useful for inspecting tokens during API debugging. Use jwt-verify when
    you have the secret/public key and want to check authenticity.

    Examples:

        pt enc jwt-decode eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.x
    """
    import json as _json

    import jwt

    try:
        header = jwt.get_unverified_header(token)
        payload = jwt.decode(token, options={"verify_signature": False})
    except Exception as exc:
        raise PolytoolError(f"Invalid JWT: {exc}") from exc

    console.print("[bold cyan]Header[/bold cyan]")
    console.print_json(_json.dumps(header))
    console.print("[bold cyan]Payload[/bold cyan]")
    console.print_json(_json.dumps(payload))


@app.command("jwt-verify")
def cmd_jwt_verify(
    token: Annotated[str, typer.Argument(help="JWT to verify")],
    secret: Annotated[
        str,
        typer.Option("--secret", "-s", help="Shared secret (HS256) or path to public key"),
    ],
    algorithm: Annotated[
        str,
        typer.Option("--alg", "-a", help="Expected algorithm (e.g. HS256, RS256)"),
    ] = "HS256",
) -> None:
    """Verify a JWT signature.

    Examples:

        pt enc jwt-verify $TOKEN --secret hunter2
        pt enc jwt-verify $TOKEN --secret pubkey.pem --alg RS256
    """
    import jwt

    key: str | bytes = secret
    if Path(secret).exists():
        key = Path(secret).read_bytes()

    try:
        payload = jwt.decode(token, key, algorithms=[algorithm])
    except jwt.InvalidSignatureError as exc:
        raise PolytoolError("Signature is INVALID.", hint="Check your key/algorithm.") from exc
    except jwt.ExpiredSignatureError as exc:
        raise PolytoolError("Token has expired.") from exc
    except Exception as exc:
        raise PolytoolError(f"JWT verification failed: {exc}") from exc

    import json as _json

    console.print("[green bold]Signature OK[/green bold]")
    console.print_json(_json.dumps(payload))

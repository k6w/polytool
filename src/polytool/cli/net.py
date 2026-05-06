"""Network helpers (port-check, ip-info, http)."""

from __future__ import annotations

import json as _json
import socket
from typing import Annotated

import typer

from polytool.core.console import console
from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="net",
    help="Network helpers (port-check, ip-info, http).",
    no_args_is_help=True,
)


@app.command("port-check")
def cmd_port_check(
    host_port: Annotated[str, typer.Argument(help="host:port, e.g. example.com:443")],
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Seconds")] = 3.0,
) -> None:
    """Check whether a TCP port is reachable.

    Examples:

        pt net port-check example.com:443
        pt net port-check 127.0.0.1:5432 --timeout 1
    """
    if ":" not in host_port:
        raise PolytoolError(
            "Argument must be host:port",
            hint="Try 'example.com:443'.",
        )
    host, port_s = host_port.rsplit(":", 1)
    try:
        port = int(port_s)
    except ValueError as exc:
        raise PolytoolError(f"Port {port_s!r} is not a number") from exc
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError as exc:
        raise PolytoolError(
            f"{host}:{port} unreachable: {exc}",
            hint="Check the host, port, and firewall.",
        ) from exc
    typer.echo(f"{host}:{port} OPEN")


@app.command("ip-info")
def cmd_ip_info(
    ip: Annotated[str | None, typer.Argument(help="IP address (default: your public IP)")] = None,
) -> None:
    """Show geo / ISP info for an IP (uses ip-api.com, no key, free tier).

    Examples:

        pt net ip-info
        pt net ip-info 8.8.8.8
    """
    import httpx

    target = ip or ""
    url = f"http://ip-api.com/json/{target}"
    try:
        r = httpx.get(url, timeout=10)
        r.raise_for_status()
    except httpx.HTTPError as exc:
        raise PolytoolError(f"Lookup failed: {exc}") from exc
    data = r.json()
    if data.get("status") != "success":
        raise PolytoolError(f"Lookup failed: {data.get('message', 'unknown')}")
    console.print_json(_json.dumps(data, indent=2))


@app.command("http")
def cmd_http(
    method: Annotated[str, typer.Argument(help="HTTP method (GET, POST, ...)")],
    url: Annotated[str, typer.Argument(help="URL")],
    headers: Annotated[
        list[str] | None,
        typer.Option("--header", "-H", help="Header 'Name: Value' (repeatable)"),
    ] = None,
    body: Annotated[str | None, typer.Option("--data", "-d", help="Request body")] = None,
    json_body: Annotated[
        str | None, typer.Option("--json", "-j", help="Request body as JSON literal")
    ] = None,
    timeout: Annotated[float, typer.Option("--timeout", help="Seconds")] = 30.0,
) -> None:
    """Make an HTTP request and pretty-print the response.

    Examples:

        pt net http GET https://api.github.com
        pt net http POST https://httpbin.org/post --json '{"k":"v"}'
        pt net http GET https://api.github.com -H "Accept: application/vnd.github+json"
    """
    import httpx

    hdrs: dict[str, str] = {}
    for h in headers or []:
        if ":" not in h:
            raise PolytoolError(f"Bad header {h!r}", hint="Format: 'Name: Value'")
        name, _, value = h.partition(":")
        hdrs[name.strip()] = value.strip()

    payload = None
    json_payload = None
    if json_body is not None:
        try:
            json_payload = _json.loads(json_body)
        except _json.JSONDecodeError as exc:
            raise PolytoolError(f"--json must be valid JSON: {exc}") from exc
    elif body is not None:
        payload = body

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.request(
                method.upper(),
                url,
                headers=hdrs,
                content=payload,
                json=json_payload,
            )
    except httpx.HTTPError as exc:
        raise PolytoolError(f"Request failed: {exc}") from exc

    color = "green" if resp.is_success else "red"
    console.print(
        f"[{color}]HTTP {resp.status_code} {resp.reason_phrase}[/{color}] {resp.http_version}"
    )
    for k, v in resp.headers.items():
        console.print(f"[cyan]{k}[/cyan]: {v}")
    console.print()
    ct = resp.headers.get("content-type", "")
    if "json" in ct:
        try:
            console.print_json(resp.text)
            return
        except Exception:
            pass
    console.print(resp.text)

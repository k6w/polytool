"""Tests for `pt net`."""

from __future__ import annotations

import socket
import threading


def test_port_check_open(runner, cli_app) -> None:
    # Spin up a transient listener on an ephemeral port.
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]

    def _accept_one():
        try:
            conn, _ = s.accept()
            conn.close()
        except OSError:
            pass

    t = threading.Thread(target=_accept_one, daemon=True)
    t.start()
    try:
        result = runner.invoke(cli_app, ["net", "port-check", f"127.0.0.1:{port}"])
    finally:
        s.close()
    assert result.exit_code == 0
    assert "OPEN" in result.stdout


def test_port_check_closed(runner, cli_app) -> None:
    # Pick an unused port — bind+release to find one, then probe it.
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    result = runner.invoke(cli_app, ["net", "port-check", f"127.0.0.1:{port}", "--timeout", "1"])
    assert result.exit_code != 0


def test_port_check_bad_format(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["net", "port-check", "no-colon-here"])
    assert result.exit_code != 0


def test_http_with_mock(runner, cli_app, monkeypatch) -> None:
    """Mock httpx so the test doesn't hit the network."""
    import httpx

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"hello": "world", "method": request.method, "url": str(request.url)},
        )

    transport = httpx.MockTransport(mock_handler)
    real_client = httpx.Client

    def fake_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", fake_client)

    result = runner.invoke(cli_app, ["net", "http", "GET", "https://api.example.com/x"])
    assert result.exit_code == 0
    assert "HTTP 200" in result.stdout
    assert "hello" in result.stdout


def test_ip_info_with_mock(runner, cli_app, monkeypatch) -> None:
    import httpx

    def fake_get(url, *args, **kwargs):
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json={
                "status": "success",
                "country": "United States",
                "isp": "Example ISP",
                "query": "8.8.8.8",
            },
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    result = runner.invoke(cli_app, ["net", "ip-info", "8.8.8.8"])
    assert result.exit_code == 0
    assert "Example ISP" in result.stdout or "United States" in result.stdout

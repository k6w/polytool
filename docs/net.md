# `pt net` — Network helpers

Check whether a TCP port is reachable, look up IP geolocation, make HTTP requests.

> No extra needed — uses base deps + `httpx`.

## Verbs

| Verb | Purpose |
|---|---|
| [`port-check`](#pt-net-port-check) | Test TCP connectivity to host:port |
| [`ip-info`](#pt-net-ip-info) | Geolocate / lookup ISP for an IP (uses ip-api.com) |
| [`http`](#pt-net-http) | Make an HTTP request and pretty-print the response |

---

## `pt net port-check`

Open a TCP connection to a host:port and report whether it succeeds.

### Synopsis

```
pt net port-check HOST:PORT [-t|--timeout SECONDS]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `HOST:PORT` | str | yes | Target — e.g. `example.com:443`. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--timeout` | `-t` | float | `3.0` | Seconds before giving up. |

### Examples

```bash
pt net port-check example.com:443
pt net port-check 127.0.0.1:5432 --timeout 1
pt net port-check db.internal:6379
```

### Output

- Success: `host:port OPEN` and exit 0.
- Failure: red error panel and exit 1.

### Errors

- `Argument must be host:port` — missed the colon.
- `Port '<x>' is not a number`
- `<host>:<port> unreachable: <reason>` — check the host/port/firewall.

---

## `pt net ip-info`

Look up geolocation, ISP, AS, and other public info for an IP. Uses [ip-api.com](https://ip-api.com)'s free tier (no API key).

### Synopsis

```
pt net ip-info [IP]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `IP` | str | no | An IP address. Omit to look up your own public IP. |

### Examples

```bash
pt net ip-info                # → your public IP info
pt net ip-info 8.8.8.8        # → Google DNS info
pt net ip-info 1.1.1.1        # → Cloudflare DNS info
```

### Output

Pretty-printed JSON with fields like `country`, `regionName`, `city`, `isp`, `org`, `as`, `query`, `lat`, `lon`, `timezone`.

### Errors

- `Lookup failed: <reason>` — typically network failure, or ip-api rate-limited you (free tier: 45 req/min per IP).

### Notes

- Free tier requires no API key but rate-limits at 45 req/min.
- For higher volume / SSL, consider [ipinfo.io](https://ipinfo.io) with a token (not yet supported by polytool).

---

## `pt net http`

Make an HTTP request and pretty-print the response — much like [HTTPie](https://httpie.io), without the dependency.

### Synopsis

```
pt net http METHOD URL [-H|--header "Name: Value"]... [-d|--data BODY] [-j|--json JSON]
                       [--timeout SECONDS]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `METHOD` | str | yes | HTTP method (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, ...). |
| `URL` | str | yes | URL. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--header` | `-H` | str (repeatable) | — | One header per `-H "Name: Value"`. |
| `--data` | `-d` | str | — | Request body (raw text). |
| `--json` | `-j` | str | — | Request body as JSON literal. Mutually preferred over `--data` for JSON APIs (sets `Content-Type: application/json`). |
| `--timeout` | — | float | `30.0` | Seconds. |

Redirects are followed (`follow_redirects=True`).

### Output

- Status line in green/red: `HTTP 200 OK HTTP/2`.
- Each response header: `Name: Value`.
- A blank line.
- Body. JSON responses are pretty-printed; everything else is dumped raw.

### Examples

```bash
pt net http GET https://api.github.com
pt net http GET https://api.github.com -H "Accept: application/vnd.github+json"
pt net http POST https://httpbin.org/post --json '{"k":"v"}'
pt net http POST https://example.com/api --data 'raw=body'
pt net http DELETE https://api.example.com/x/123 -H "Authorization: Bearer $TOKEN"
```

### Errors

- `Bad header '<x>'` — missing colon. Use `-H "Name: Value"`.
- `--json must be valid JSON` — fix the JSON literal.
- `Request failed: <reason>` — network/DNS/TLS error from httpx.

### Notes

- The status panel goes to stdout (not stderr), so you can pipe the body through `jq` / `less` / etc. when JSON.
- HTTP/2 is supported automatically (httpx).

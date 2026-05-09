# `pt enc` — Hashing and encoding

Cryptographic and fast hashes, base64 / URL / HTML encode-decode, JWT decode and verify.

> No extra needed — uses base deps.

## Verbs

| Verb | Purpose |
|---|---|
| [`hash`](#pt-enc-hash) | md5/sha1/sha256/sha512/blake2b/xxhash |
| [`base64`](#pt-enc-base64) | Base64 encode / decode (standard or URL-safe) |
| [`url`](#pt-enc-url) | URL-encode / decode a string |
| [`html`](#pt-enc-html) | HTML escape / unescape a string |
| [`jwt-decode`](#pt-enc-jwt-decode) | Decode a JWT without signature verification |
| [`jwt-verify`](#pt-enc-jwt-verify) | Verify a JWT signature against a key |

---

## `pt enc hash`

Compute a hash digest of a file or stdin.

### Synopsis

```
pt enc hash ALGORITHM [SOURCE]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `ALGORITHM` | enum | yes | One of: `md5`, `sha1`, `sha256`, `sha512`, `blake2b`, `xxhash`. |
| `SOURCE` | path | no | File path. Use `-` or omit for stdin. |

### Examples

```bash
pt enc hash sha256 release.zip
echo -n "hello" | pt enc hash sha256
pt enc hash xxhash huge.iso              # very fast non-crypto hash
pt enc hash md5 download.iso             # legacy mirrors still publish md5
pt enc hash blake2b file.bin
```

### Notes

- `xxhash` produces a 16-character hex digest (xxh3_64). It's not cryptographic, but ~10× faster than sha256 — great for de-duping or change detection.
- For verifying a downloaded artifact, prefer `sha256` or `blake2b`.
- The output is a single line: just the hex digest. Compare with `cmp` / `==` in scripts.

---

## `pt enc base64`

Base64 encode or decode.

### Synopsis

```
pt enc base64 encode|decode [SOURCE] [--urlsafe|--standard]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `mode` | enum | yes | `encode` or `decode`. |
| `SOURCE` | path | no | File for encode / text file for decode. Use `-` or omit for stdin. |

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--urlsafe` / `--standard` | flag | `--standard` | URL-safe alphabet (`-`/`_` instead of `+`/`/`). |

### Examples

```bash
pt enc base64 encode README.md
echo -n "hello" | pt enc base64 encode
pt enc base64 decode encoded.txt
echo "aGVsbG8=" | pt enc base64 decode

# URL-safe (e.g. for query strings)
pt enc base64 encode --urlsafe payload.bin
```

### Notes

- Decode emits the original bytes. If they're valid UTF-8, you'll see a string; otherwise the raw bytes are written to stdout (so binary roundtrips are safe).

### Errors

- `Invalid base64 input: <reason>` — malformed input. Pass `--urlsafe` if appropriate.

---

## `pt enc url`

URL-encode or decode a string.

### Synopsis

```
pt enc url encode|decode [TEXT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `mode` | enum | yes | `encode` or `decode`. |
| `TEXT` | str | no | The text. If omitted, reads stdin. |

### Examples

```bash
pt enc url encode "hello world & friends"
# → hello%20world%20%26%20friends

pt enc url decode "hello%20world%20%26%20friends"
# → hello world & friends

echo "weird text @#$" | pt enc url encode
```

### Notes

- Uses `urllib.parse.quote` with `safe=""` — no characters left untouched. Use a different tool if you need RFC 3986 path-vs-query nuance.

---

## `pt enc html`

HTML-escape or unescape a string.

### Synopsis

```
pt enc html encode|decode [TEXT]
```

### Examples

```bash
pt enc html encode "<script>alert(1)</script>"
# → &lt;script&gt;alert(1)&lt;/script&gt;

pt enc html decode "&lt;b&gt;hi&lt;/b&gt;"
# → <b>hi</b>
```

---

## `pt enc jwt-decode`

Decode a JWT and print its header and payload as JSON. **Does NOT verify the signature** — use `jwt-verify` for that.

### Synopsis

```
pt enc jwt-decode TOKEN
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `TOKEN` | str | yes | A JWT (`header.payload.signature`). |

### Output

Two sections, both pretty-printed JSON:
- `Header` (the algorithm and metadata)
- `Payload` (the claims)

### Examples

```bash
pt enc jwt-decode eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.<sig>
```

### Notes

- This is intended for debugging — useful for seeing what claims a service issued you.
- Even though signature is not verified, the token must be syntactically a JWT (3 dot-separated base64-url segments). Garbage input produces an error.

---

## `pt enc jwt-verify`

Verify a JWT signature against a secret (HS*) or a public key file (RS*/ES*).

### Synopsis

```
pt enc jwt-verify TOKEN -s|--secret KEY [-a|--alg ALG]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `TOKEN` | str | yes | The JWT. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--secret` | `-s` | str/path | **required** | Shared secret string (for HS*) **or** a path to a public key file (for RS*/ES*). |
| `--alg` | `-a` | str | `HS256` | Expected algorithm. |

If `--secret` is the path to an existing file, the file is read as bytes and used as the key (use this for `RS256` etc.).

### Examples

```bash
# HMAC
pt enc jwt-verify $TOKEN --secret hunter2

# RSA
pt enc jwt-verify $TOKEN --secret ./pubkey.pem --alg RS256

# ECDSA
pt enc jwt-verify $TOKEN --secret ./ec-pub.pem --alg ES256
```

### Output

- On success: prints `Signature OK` (green) followed by the claims as JSON, exits 0.
- On failure: red error panel, exits 1.

### Errors

- `Signature is INVALID.` — the signature doesn't match.
- `Token has expired.` — the `exp` claim is in the past.
- `JWT verification failed: <reason>` — other PyJWT failures (bad alg, malformed token, ...).

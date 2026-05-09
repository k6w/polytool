# `pt data` — Data format converter

Convert between JSON, YAML, TOML, CSV, and XML; pretty-print structured data; validate that a file parses.

> No extra needed — uses base deps (stdlib `json`, `tomllib`; `ruamel.yaml`, `tomli-w`, `xmltodict`).

## Verbs

| Verb | Purpose |
|---|---|
| [`convert`](#pt-data-convert) | Convert between formats |
| [`pretty`](#pt-data-pretty) | Pretty-print, keeping the same format |
| [`validate`](#pt-data-validate) | Exit 0/1 depending on whether a file parses |

## Format detection

When `--from` isn't passed, the source format is detected from the file extension:

| Extension | Format |
|---|---|
| `.json` | JSON |
| `.yaml`, `.yml` | YAML |
| `.toml` | TOML |
| `.csv` | CSV (each row → dict, first row = headers) |
| `.xml` | XML |

If reading from stdin, you must pass `--from` explicitly.

## Format compatibility

| Source\Target | json | yaml | toml | csv | xml |
|---|---|---|---|---|---|
| **json** | ✓ | ✓ | ✓¹ | ✓² | ✓³ |
| **yaml** | ✓ | ✓ | ✓¹ | ✓² | ✓³ |
| **toml** | ✓ | ✓ | ✓ | ✓² | ✓³ |
| **csv** | ✓ | ✓ | — | ✓ | — |
| **xml** | ✓ | ✓ | ✓¹ | — | ✓ |

- ¹ Output to TOML requires the top-level value be a mapping (object/dict).
- ² Output to CSV requires a list of objects with consistent keys.
- ³ Output to XML requires a single top-level mapping (e.g. `{"root": {...}}`).

Combinations marked `—` will produce a friendly error explaining the constraint.

---

## `pt data convert`

Convert from one format to another.

### Synopsis

```
pt data convert [SOURCE] [-t|--to FORMAT] [-f|--from FORMAT] [-o|--output OUTPUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | no | Source file. Use `-` or omit for stdin. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--to` | `-t` | enum | `json` | Target format: `json` `yaml` `toml` `csv` `xml`. |
| `--from` | `-f` | enum | from extension | Source format. **Required when reading from stdin.** |
| `--output` | `-o` | path | stdout | Output file. |

### Examples

```bash
pt data convert config.yaml --to json
pt data convert data.csv --to json -o data.json
cat x.toml | pt data convert --from toml --to yaml
pt data convert tasks.json --to csv -o tasks.csv

# CSV-friendly JSON: a list of records
echo '[{"name":"a","val":1},{"name":"b","val":2}]' | pt data convert --from json --to csv
```

### Errors

- `Cannot detect format from extension '<ext>'` — pass `--from`.
- `Cannot detect format from stdin` — pass `--from`.
- `TOML output requires a top-level mapping` — wrap your list in a key.
- `CSV output requires a list of records` / `requires a list of dicts` — only flat object arrays convert cleanly.
- `XML output requires a top-level mapping` — wrap data in a single root key.
- `Unknown format '<x>'` — typos in `--from` / `--to`.

---

## `pt data pretty`

Pretty-print a file in the same format. Most useful for noisy single-line JSON/YAML.

### Synopsis

```
pt data pretty [SOURCE] [-f|--from FORMAT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | no | Source file. Use `-` or omit for stdin. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--from` | `-f` | enum | from extension | Source format. |

Output goes to stdout.

### Examples

```bash
pt data pretty messy.json
echo '{"a":1,"b":[2,3]}' | pt data pretty --from json
```

---

## `pt data validate`

Parse the file. Exit `0` if it's valid; exit `1` (with a red error panel) if it isn't.

### Synopsis

```
pt data validate [SOURCE] [-f|--from FORMAT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | no | Source file. Use `-` or omit for stdin. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--from` | `-f` | enum | from extension | Source format. |

### Examples

```bash
pt data validate config.yaml
cat x.json | pt data validate --from json
pt data validate corrupt.toml ; echo $?    # → 1
```

### Use in CI

```bash
# Fail the build if any committed YAML doesn't parse
git ls-files '*.yaml' '*.yml' | xargs -I{} pt data validate {}
```

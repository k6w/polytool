# `pt gen` — Generators

Strong passwords, UUIDs (v1/v3/v4/v5/v7), lorem ipsum / fake text.

> No extra needed — uses base deps + `faker`.

## Verbs

| Verb | Purpose |
|---|---|
| [`password`](#pt-gen-password) | Cryptographically strong passwords |
| [`uuid`](#pt-gen-uuid) | UUID v1, v3, v4, v5, v7 |
| [`lorem`](#pt-gen-lorem) | Lorem ipsum / fake text in many locales |

---

## `pt gen password`

Generate one or more cryptographically random passwords using `secrets`.

### Synopsis

```
pt gen password [-n|--length N] [-c|--count N] [--no-symbols]
```

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--length` | `-n` | int | `24` | Password length. Minimum `4`. |
| `--count` | `-c` | int | `1` | How many to generate (one per line). |
| `--no-symbols` | — | flag | off | Letters and digits only. |

### Default alphabet

`a-z A-Z 0-9 ! @ # $ % ^ & * ( ) - _ = + [ ] { } ; : , . ?`

With `--no-symbols`: `a-z A-Z 0-9` only.

### Examples

```bash
pt gen password                              # 24 chars, with symbols
pt gen password --length 32                  # 32 chars
pt gen password --count 5 --no-symbols       # 5 alphanumeric passwords
pt gen password -n 64 -c 1                   # one 64-char password
```

### Errors

- `--length must be at least 4` — too short to be useful.

### Notes

- Uses `secrets.choice` so it's safe for production use.

---

## `pt gen uuid`

Generate one or more UUIDs.

### Synopsis

```
pt gen uuid [VERSION] [-c|--count N] [--namespace NS] [--name NAME]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `VERSION` | enum | no, default `v4` | `v1`, `v3`, `v4`, `v5`, or `v7`. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--count` | `-c` | int | `1` | How many to generate. |
| `--namespace` | — | enum | — | Namespace for v3/v5: `dns`, `url`, `oid`, `x500`. |
| `--name` | — | str | — | Name for v3/v5. |

### Versions

- **v1** — time + MAC. Discloses your MAC address; not recommended for new use.
- **v3** — namespace + name (MD5). `--namespace` and `--name` required.
- **v4** — random (the most commonly used).
- **v5** — namespace + name (SHA1). `--namespace` and `--name` required.
- **v7** — time-ordered random (Python 3.13+; great for database PKs because it sorts chronologically).

### Examples

```bash
pt gen uuid                                  # v4 (default)
pt gen uuid v7                               # time-sortable
pt gen uuid v4 --count 10                    # 10 random UUIDs
pt gen uuid v5 --namespace dns --name example.com
pt gen uuid v3 --namespace url --name "https://example.com/x"
```

### Errors

- `v3 requires --namespace and --name` — pass both.
- `Unknown namespace '<x>'` — pick from `dns`, `url`, `oid`, `x500`.
- `Unsupported UUID version '<x>'` — typo.

---

## `pt gen lorem`

Generate placeholder text. Powered by [`faker`](https://faker.readthedocs.io/), so you can pick a locale.

### Synopsis

```
pt gen lorem [-p|--paragraphs N] [-s|--sentences N] [-w|--words N] [--locale LOCALE]
```

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--paragraphs` | `-p` | int | `1` | Number of paragraphs. Ignored if `--words` is given. |
| `--sentences` | `-s` | int | random | Sentences per paragraph. Default = random 3-7 per paragraph. |
| `--words` | `-w` | int | — | Generate exactly N space-separated words. Overrides paragraphs. |
| `--locale` | — | str | `en_US` | Faker locale (`fr_FR`, `de_DE`, `ja_JP`, `es_ES`, ...). See Faker's locale list. |

### Examples

```bash
pt gen lorem                            # one paragraph
pt gen lorem --paragraphs 3
pt gen lorem --words 50                 # exactly 50 words
pt gen lorem --paragraphs 2 --sentences 4
pt gen lorem --locale fr_FR             # French
pt gen lorem --locale ja_JP             # Japanese
```

### Errors

- `--paragraphs must be >= 1`
- `--words must be >= 1`

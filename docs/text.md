# `pt text` — Text utilities

Diff two files, count lines/words/chars, convert string casing, slugify, render Markdown.

> No extra needed — uses base deps + `python-slugify` + `markdown-it-py`.

## Verbs

| Verb | Purpose |
|---|---|
| [`diff`](#pt-text-diff) | Unified diff between two files |
| [`wc`](#pt-text-wc) | Line / word / char count |
| [`case`](#pt-text-case) | Convert casing (snake/kebab/camel/pascal/...) |
| [`slugify`](#pt-text-slugify) | URL-friendly slug |
| [`md-to-html`](#pt-text-md-to-html) | Render Markdown to HTML |
| [`md-preview`](#pt-text-md-preview) | Render Markdown in the terminal |

---

## `pt text diff`

Unified diff between two text files (Python's `difflib.unified_diff`).

### Synopsis

```
pt text diff A B [-u|--unified N]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `A` | path | yes | First file. |
| `B` | path | yes | Second file. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--unified` | `-u` | int | `3` | Lines of context around each change. |

### Examples

```bash
pt text diff a.txt b.txt
pt text diff old.cfg new.cfg --unified 5
```

---

## `pt text wc`

Print line, word, and char counts.

### Synopsis

```
pt text wc [SOURCE]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | no | File. Omit / `-` for stdin. |

### Output

```
lines: 42
words: 314
chars: 2048
```

### Examples

```bash
pt text wc README.md
cat README.md | pt text wc
```

---

## `pt text case`

Convert string casing.

### Synopsis

```
pt text case STYLE [TEXT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `STYLE` | enum | yes | One of: `snake`, `kebab`, `camel`, `pascal`, `constant`, `title`, `upper`, `lower`. |
| `TEXT` | str | no | The text. Omit for stdin. |

### Style examples (input: `Hello World foo-bar`)

| Style | Output |
|---|---|
| `snake` | `hello_world_foo_bar` |
| `kebab` | `hello-world-foo-bar` |
| `camel` | `helloWorldFooBar` |
| `pascal` | `HelloWorldFooBar` |
| `constant` | `HELLO_WORLD_FOO_BAR` |
| `title` | `Hello World Foo-Bar` |
| `upper` | `HELLO WORLD FOO-BAR` |
| `lower` | `hello world foo-bar` |

### Examples

```bash
pt text case snake "Hello World"            # → hello_world
pt text case camel "user-id-token"          # → userIdToken
pt text case pascal "user_id_token"         # → UserIdToken
pt text case constant "fooBarBaz"           # → FOO_BAR_BAZ
echo "hello there" | pt text case kebab     # → hello-there
```

---

## `pt text slugify`

URL-friendly slug. Strips diacritics, lowercases, collapses non-alphanumerics.

### Synopsis

```
pt text slugify [TEXT] [--sep SEP]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `TEXT` | str | no | Text. Omit for stdin. |

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--sep` | str | `-` | Separator. |

### Examples

```bash
pt text slugify "Hello, World! Café"        # → hello-world-cafe
pt text slugify "My Post Title" --sep _     # → my_post_title
echo "Über uns" | pt text slugify           # → uber-uns
```

---

## `pt text md-to-html`

Convert Markdown to HTML using `markdown-it-py` (CommonMark + tables + strikethrough).

### Synopsis

```
pt text md-to-html [SOURCE] [-o|--output OUTPUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | no | Markdown file. Omit / `-` for stdin. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | stdout | Output HTML file. |

### Examples

```bash
pt text md-to-html README.md -o README.html
cat post.md | pt text md-to-html
```

### Notes

- HTML in the source Markdown is passed through (the `html: true` option is enabled).
- Tables and strikethrough (`~~`) extensions are enabled.

---

## `pt text md-preview`

Render Markdown in the terminal using Rich's Markdown renderer.

### Synopsis

```
pt text md-preview [SOURCE]
```

### Examples

```bash
pt text md-preview README.md
cat post.md | pt text md-preview
```

### Notes

- Uses your terminal's color theme (looks great in any modern terminal).
- For lots of content, pipe to a pager: `pt text md-preview big.md | less -R`.

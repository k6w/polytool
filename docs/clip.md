# `pt clip` — Clipboard

Read and write the system clipboard via [`pyperclip`](https://github.com/asweigart/pyperclip).

> No extra needed — base dep.

## Verbs

| Verb | Purpose |
|---|---|
| [`copy`](#pt-clip-copy) | Copy text to the clipboard |
| [`paste`](#pt-clip-paste) | Print clipboard contents to stdout |

---

## `pt clip copy`

### Synopsis

```
pt clip copy [TEXT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `TEXT` | str | no | Text. Omit (or pass `-`) to read stdin. |

### Examples

```bash
pt clip copy "hello"
echo -n "secret token" | pt clip copy
cat ssh-public-key.pub | pt clip copy
```

### Output

A status line like `Copied 32 chars.` on stderr.

### Errors

- `Clipboard not available: <reason>` — see Notes.

---

## `pt clip paste`

### Synopsis

```
pt clip paste
```

### Examples

```bash
pt clip paste
pt clip paste > saved.txt
pt clip paste | pt text slugify          # paste -> slugify roundtrip
```

### Errors

- `Clipboard not available: <reason>` — see Notes.

---

## Notes

- **Windows / macOS**: works out of the box, no extra deps.
- **Linux X11**: requires `xclip` or `xsel`. Install with `sudo apt-get install xclip`.
- **Linux Wayland**: requires `wl-clipboard`. Install with `sudo apt-get install wl-clipboard`.
- **Headless Linux** (CI): no display, no clipboard. polytool prints a hint pointing at xclip — but typically you don't need clipboard in headless contexts.

# `pt file` — File operations

Batch rename, find duplicates, list big files, organize by extension/date, archive into zip/tar/7z.

> Base deps cover everything except 7z (`[archive]`).

## Verbs

| Verb | Purpose |
|---|---|
| [`rename`](#pt-file-rename) | Batch rename files matching a glob |
| [`dedupe`](#pt-file-dedupe) | Find / delete duplicate files (size-then-sha256) |
| [`bigfiles`](#pt-file-bigfiles) | List the largest files in a directory tree |
| [`organize`](#pt-file-organize) | Move files into subfolders by extension or date |
| [`archive`](#pt-file-archive) | Create zip / tar / tar.gz / tar.bz2 / tar.xz / 7z |

---

## `pt file rename`

Batch rename files matching a glob, using a template.

### Synopsis

```
pt file rename PATTERN --to TEMPLATE [-d|--dir DIR] [--start N] [--dry-run]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `PATTERN` | str | yes | Glob — e.g. `*.JPG`, `IMG_*.png`. Quote in shells that expand globs. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--to` | — | str | **required** | New-name template. Placeholders: `{name}` (stem), `{ext}` (extension without dot), `{n}` / `{n:03}` (running counter). |
| `--dir` | `-d` | path | `.` | Directory to scan (non-recursive). |
| `--start` | — | int | `1` | Starting value for `{n}`. |
| `--dry-run` | — | flag | off | Print planned renames; don't touch the disk. |

### Examples

```bash
# Lowercase all .JPG to .jpg
pt file rename "*.JPG" --to "{name}.jpg"

# Sequence images
pt file rename "IMG_*.png" --to "photo_{n:03}.png"

# Add a prefix
pt file rename "*.txt" --to "draft_{name}.{ext}"

# See what would happen first
pt file rename "*.tmp" --to "{name}.bak" --dry-run
```

### Errors

- `No files matched '<pattern>' in <dir>` — bad glob or empty directory.
- `Target exists: <path>` — refuses to overwrite. Rename the existing file or pick a different template.

### Notes

- The matching is non-recursive (only files in `--dir`, not subdirectories). For recursive renames, run per directory.
- Templates use Python's `str.format`, so all of `{n:03}`, `{n:d}`, etc. work.

---

## `pt file dedupe`

Find duplicate files in a directory tree (by size then SHA-256). Optionally delete duplicates, keeping one copy.

### Synopsis

```
pt file dedupe DIRECTORY [--delete] [--keep first|shortest]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `DIRECTORY` | path | yes | Directory to scan recursively. |

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--delete` | flag | off (dry run) | Actually remove duplicates. Without this, only prints what would be removed. |
| `--keep` | enum | `first` | Which copy to keep: `first` (lexicographically first path) or `shortest` (shortest path string). |

Output (stderr) lists each duplicate that would be / was removed:

```
dup /Downloads/big.zip  (keep /Documents/big.zip)
dup /Downloads/big (1).zip  (keep /Documents/big.zip)
```

A summary line on stdout reports the count and bytes reclaimed.

### Examples

```bash
# Safe preview
pt file dedupe ~/Downloads

# Actually delete
pt file dedupe ~/Downloads --delete

# Keep the shortest path version
pt file dedupe ~/projects/assets --delete --keep shortest
```

### Notes

- Files of size 0 and groups of 1 are skipped.
- Hashing happens only when there are ≥2 files of the same size — fast even on large trees.

---

## `pt file bigfiles`

List the largest files under a directory.

### Synopsis

```
pt file bigfiles [DIRECTORY] [-n|--top N]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `DIRECTORY` | path | no | Directory (default: `.`). |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--top` | `-n` | int | `20` | How many to show. |

Output (one per line):

```
   3.4 GB  ./Videos/some-big.mp4
   1.2 GB  ./Downloads/dataset.zip
 850.0 MB  ./.cache/huge.cache
```

### Examples

```bash
pt file bigfiles
pt file bigfiles ~/Downloads --top 50
pt file bigfiles . -n 5
```

### Notes

- Walks recursively. Files we can't `stat()` (permission errors, broken symlinks) are skipped.

---

## `pt file organize`

Move files in a directory into subfolders by extension or by year-month modified.

### Synopsis

```
pt file organize DIRECTORY [--by extension|date] [--dry-run]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `DIRECTORY` | path | yes | Directory to organize (non-recursive — only direct children move). |

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--by` | enum | `extension` | `extension` (subfolder per extension) or `date` (subfolder per `YYYY-MM` of mtime). |
| `--dry-run` | flag | off | Print the moves; don't perform them. |

### Examples

```bash
# Move all .pdf into pdf/, all .jpg into jpg/, etc.
pt file organize ~/Downloads

# Group by year-month modified
pt file organize ~/Pictures --by date

pt file organize ~/Downloads --dry-run
```

### Notes

- Files without an extension go into a `no-extension/` subfolder.
- Operates only on direct children (not recursive). Run per subdirectory if needed.

### Errors

- `Unknown --by value '<x>'` — pick `extension` or `date`.

---

## `pt file archive`

Create an archive from one or more files/folders. Format is picked from the output extension.

### Synopsis

```
pt file archive PATHS... -o|--output OUTPUT
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `PATHS...` | path[] | yes (≥1) | Files and/or folders to include. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | **required** | Output archive. |

### Supported output extensions

| Extension | Format | Notes |
|---|---|---|
| `.zip` | ZIP (deflate) | stdlib |
| `.tar` | uncompressed TAR | stdlib |
| `.tar.gz` / `.tgz` | gzipped TAR | stdlib |
| `.tar.bz2` | bzip2 TAR | stdlib |
| `.tar.xz` | xz TAR | stdlib |
| `.7z` | 7-Zip | requires `[archive]` (`py7zr`) |

### Examples

```bash
pt file archive ./project --output project.zip
pt file archive a.txt b.txt --output bundle.tar.gz
pt file archive ./big_folder --output big.7z
pt file archive docs/ src/ tests/ --output snapshot.tar.xz
```

### Errors

- `Unsupported archive type '<.suffix>'` — pick from the table above.
- `Missing optional dependency: 'py7zr'` — install `[archive]` for `.7z`.

### Notes

- Folders are added with their basename as the top-level entry (so extracting `project.zip` yields `./project/...`).

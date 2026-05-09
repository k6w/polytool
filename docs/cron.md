# `pt cron` — Cron expression utilities

Translate a cron expression into English; print the next N firings.

> No extra needed — uses `croniter` + `cron-descriptor`.

## Verbs

| Verb | Purpose |
|---|---|
| [`explain`](#pt-cron-explain) | Render expression in English |
| [`next`](#pt-cron-next) | Show the next N firing times (UTC) |

---

## `pt cron explain`

### Synopsis

```
pt cron explain "EXPRESSION"
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `EXPRESSION` | str | yes | Standard 5-field cron (minute hour dom month dow). Quote it because `*` is a shell glob. |

### Examples

```bash
pt cron explain "0 9 * * MON"
# → At 09:00 AM, only on Monday

pt cron explain "*/5 * * * *"
# → Every 5 minutes

pt cron explain "0 0 1 * *"
# → At 12:00 AM, on day 1 of the month

pt cron explain "30 14 * * 1-5"
# → At 02:30 PM, Monday through Friday
```

### Errors

- `Invalid cron expression: <reason>` — `cron-descriptor` couldn't parse the expression.

---

## `pt cron next`

### Synopsis

```
pt cron next "EXPRESSION" [-n|--count N]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `EXPRESSION` | str | yes | Standard 5-field cron. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--count` | `-n` | int | `5` | How many upcoming firings to show. |

Output: one ISO-8601 datetime per line, in UTC.

### Examples

```bash
pt cron next "0 9 * * MON"
# 2026-05-11T09:00:00+00:00
# 2026-05-18T09:00:00+00:00
# 2026-05-25T09:00:00+00:00
# 2026-06-01T09:00:00+00:00
# 2026-06-08T09:00:00+00:00

pt cron next "*/15 * * * *" --count 10
```

### Notes

- All times are computed in UTC (not your local time). Convert with `pt convert timestamp ... --to iso` if you want local-zone output by passing the `+offset` form.

### Errors

- `Invalid cron expression: <reason>` — `croniter` rejected the expression.

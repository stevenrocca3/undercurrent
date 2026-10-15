# Synthetic fixtures F1-F17

These fixtures implement `01-event-semantics.md` v0.2, §7 (F01-F13), plus F14-F17, which cover the quarantine and registry rules decided on 2026-10-14 (see `SPEC-GAPS.md`). The verifier agent wrote them, and Steven hand-checks them. **Expected outputs are hand-authored from the reasoning in each fixture's README. No code computes them.** `generate_inputs.py` only writes the `input/*.json.gz` files, from literal strings. Two special cases: F16 is a gzip stream cut at a sync-flush point, and F17 hour 1 is raw non-gzip bytes.

Every fixture except F01 is **F01 plus one anomaly**. F01's hour-0 file (6 lines: B1..B6) is reused byte for byte. So check F01 first; each other fixture's expected output is F01's plus a small delta, explained in its README.

Assumptions the spec does not pin down are listed in `SPEC-GAPS.md`, and each fixture README points to the ones it depends on.

## Index

| Fixture | Case | Key expected numbers |
|---|---|---|
| F01-clean-hour | clean hour, mixed types | canonical 6; Push 2 / Watch 3 / Issues 1; stars 501 = 2, 502 = 1 |
| F02-dup-within-file | exact duplicate in one file | canonical 7; r3 6,1,0; r4 unchanged from F01 |
| F03-dup-across-files | exact duplicate across hour 0 and hour 1 | canonical 8; r3 7,1,0; kept occurrence is hour 0 line 4, not hour 1 line 1 |
| F04-conflicting-dup | same id, different repo | canonical 7; r3 6,1,1; r4 unchanged (first occurrence kept) |
| F05-malformed-json | truncated JSON line at line 4 | Q1 1, canonical 6; everything else as F01 |
| F06-missing-required-field | missing id / repo.id / type (+ bad date) / payload | Q2 4, canonical 7; missing actor.login is NOT quarantined |
| F07-late-event | event_time 1 s before file hour − 1h | late 1 (boundary row exactly at −1h not late); r4 row on 2026-08-31 |
| F08-future-skewed | event_time 1 s after file hour + 2h | future_skewed 1 (boundary row exactly at +2h not flagged) |
| F09-missing-hour | hours 0..2 requested, hour 1 absent | registry present/missing/present; no hour-01 rows anywhere |
| F10-unrecognized-type | `MysteryEvent` | unrecognized_type 1; kept in r2; GollumEvent not flagged |
| F11-repo-renamed | 501 renamed; 503 takes the old name | r4 501 = 3, 503 = 1 (keyed by repo_id) |
| F12-point-in-time-trap | event before t, available after t | r5 at 08:00: 501 = 2; at 09:00: 501 = 3; window-start boundary at t3 |
| F13-repeat-stars-one-actor | one actor stars one repo 3 times | r4 501 = 4 |
| F14-q3-bad-timestamp | month-13 date; bad date + numeric id | Q3 2 (Q3 beats Q4), canonical 7; `-02:00` offset date is canonical and lands at 00:50Z → 502 = 2 |
| F15-q4-wrong-id-type | numeric id; string repo.id; string actor.id | Q4 3, canonical 7; string org.id is NOT Q4 |
| F16-truncated-hour | F01 gzip cut mid-line 5 | registry truncated; canonical 4, Q1 1; 501 = 1, 502 = 1 |
| F17-unreadable-hour | hour 1 is plain JSON, not gzip | registry present/unreadable; everything else as F01 |

## Layout

```
fixtures/
  README.md            this file
  SPEC-GAPS.md         assumptions the spec does not fix; Steven decides each one
  event_types.txt      recognized GitHub event types, one per line (exact, case-sensitive match)
  generate_inputs.py   writes every fixture's input/*.json.gz from literal lines
  FNN-name/
    fixture.json       {"id","title","requested_hours":[first,last] inclusive,"cutoffs":[...]}
    README.md          every input line with its intent; every expected number derived in prose
    input/YYYY-MM-DD-H.json.gz   GH Archive naming, hour NOT zero-padded
    expected/r1.csv r2.csv r3.csv r4.csv r5.csv registry.csv flags.csv
```

Regenerate inputs with `python3 fixtures/generate_inputs.py`. Output is deterministic: fixed order, `\n` endings, gzip `mtime=0`, empty gzip filename field.

## Input conventions

- `source_file_hour` comes from the file name: `2026-09-01-2.json.gz` → `2026-09-01T02:00:00Z`.
- `source_line` is 1-based.
- All files are historical backfill: `available_at = source_file_hour + 1h + 6h` (L = 6h). For example, hour 0 → 07:00 the same day.
- `requested_hours` is an inclusive `[first, last]` pair of hour starts. The registry has exactly one row per hour in it.

## CSV conventions

General:
- Header row, comma-separated, LF line endings, trailing LF after the last row, no quoting unless needed (none of these fixtures needs any).
- Timestamps as `YYYY-MM-DDTHH:MM:SSZ`, dates as `YYYY-MM-DD`.
- Rows sorted ascending by every column, left to right. Text columns compare by **byte order** (C locale, so `Q1` < `canonical` and `GollumEvent` < `IssuesEvent`). Numeric columns compare numerically. Every repo_id in these fixtures has 3 digits, so the two orders agree.
- Zero-count rows are omitted, **except** in r1, flags and r3, which always list every row.

| File | Columns | Meaning |
|---|---|---|
| r1.csv | `line_status,count` | Rows always present, in byte order: `Q1,Q2,Q3,Q4,canonical`. canonical = lines that became canonical records *before* dedup. canonical + all Q* = total input lines. |
| r2.csv | `source_file_hour,event_type,event_count` | After dedup, attributed to the kept occurrence's `source_file_hour`. Includes unrecognized types. |
| r3.csv | `distinct_event_ids,duplicate_count,conflict_count` | Single row. duplicate_count = discarded occurrences. conflict_count = discarded occurrences whose `record_hash` differs from the kept one (a subset of duplicate_count). |
| r4.csv | `repo_id,event_date,star_events` | `WatchEvent` with `payload.action="started"`, after dedup, by UTC date of `event_time`. |
| r5.csv | `cutoff,repo_id,star_events` | For each cutoff `t` in fixture.json: star events with `event_time` in `[t−7d, t)` AND `available_at <= t`, after dedup. |
| registry.csv | `source_file_hour,status` | One row per requested hour: `present / missing / truncated / unreadable`. |
| flags.csv | `flag,count` | Rows always present, in byte order: `future_skewed,late,unrecognized_type`. Counted over kept (deduplicated) canonical records. |

Note on row order: "sorted ascending by every column" puts r1 in the order `Q1..Q4,canonical` and flags in the order `future_skewed,late,unrecognized_type`. That differs from the order the rows are named in the task brief. See SPEC-GAPS G8.

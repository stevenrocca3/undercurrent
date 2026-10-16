# Reference: `--available-at` manifest (02 §8.2)

**File:** `reference/reference.py` (320 → 347 lines, inside the ~350 limit in 01 §6). **Hidden from the other agents** by the `*-reference-*` name.

**What changed.**
- **`run`** takes `--available-at FILE`. **`fixtures`** reads `available_at.csv` next to `fixture.json` when one is present.
- **`read_manifest`** turns the CSV into `{hour_us: available_at_us}`. `parse_ts` accepts ISO-8601 with an offset, up to µs (`datetime.fromisoformat`), and rejects a value without an offset.
- **`load`** fills a new `hours (hour_us, avail_us)` table, one row per requested hour, using the manifest value or `hour + (1 + L)h`.
- **R5** joins `kept` to `hours` and tests `avail_us <= t`. It used to compute `hour_us + (1 + L)h` inline. Without a manifest the result is identical, because the same formula now lives in one place.

**Checks.**
- **`./check.sh`:** 27/27 fixtures for both implementations, so behaviour without a manifest is unchanged.
- **Throwaway probe on F12's input** (cutoffs 08:00 and 09:00):
  - With no manifest, R5 matched F12's expected output.
  - With hour 02 observed at 03:04:05.5Z, its star counts at 08:00: repo 501 went from 2 to 3.
  - With hour 01 observed at 08:00:00.000001Z, it drops out at 08:00 by 1 µs: repo 502 went from 2 to 1.
  - A naive timestamp raises `ValueError`.
- The real cases are the verifier's fixtures (`briefs/verifier-live-fixtures.md`).

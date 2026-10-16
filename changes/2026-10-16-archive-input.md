# Flat input from the fetcher's archive (`tools/archive_input.py`)

**Why:** this closes the "archive layout vs input layout" item in `2026-10-16-fetcher-cross-check.md`.
- The fetcher stores `archive/YYYY-MM-DD-H/<sha256>.json.gz`, but both implementations read a flat `YYYY-MM-DD-H.json.gz` folder.
- 02 §6 says the file for each hour comes from the fetch log's final outcome, never from a listing of the archive.
- Gate 2 needs one neutral way to build that folder for the reference side.

**What:** `python tools/archive_input.py ROOT OUT_DIR`. It uses the standard library only and imports neither implementation.
- **Linked:** each `success` or `deadline` row that names a file gets `OUT_DIR/YYYY-MM-DD-H.json.gz`, a symlink to the archived file.
- **Not linked:** a `deadline` row with no file means a `missing` hour. `late`, `republished` and the other outcomes are never linked.
- **Stops (exit 1):** when an hour has more than one final outcome, or when a named file is absent or its SHA-256 differs from the log (02 §8.4).
- **Not checked here:** the rest of §8.4 (every archived file referenced by a row; no tracked hour without a final outcome). Hours still inside their window legitimately have no final row yet. That check belongs to the Gate 2 consistency step.

**Tests:** `tools/test_archive_input.py` covers final outcomes only, two final rows, and a hash mismatch. It's added to `./check.sh`, which passes.

**Also:** AGENTS.md
- Lists the tool.
- Names the main session "reference author and scrum master", with `briefs/` in its writes, so it matches the Autonomy section.
- Points agents to report to it.

**Live run (Steven approved):** I ran it on the VM's fetcher root (`/home/opc/undercurrent-data/fetcher`), into a temporary folder that was deleted after.
- 9 `success` hours were linked, all hashes matched, and it exited 0.
- 11 `pending` rows were ignored.
- The archive's 9 hour folders were all linked.
- See `BENCHMARKS.md`.
- Don't `cut -d,` the fetch log: `Last-Modified` values contain a comma. Read it with a CSV parser.

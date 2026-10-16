# AGENTS.md: read this first

For every AI agent working in this repo: Claude, Gemini, Copilot, Codex or any other. It holds the facts you need so you don't guess. **If something you need isn't here or in the spec, stop and ask Steven. Don't invent it.**

## What this is

**undercurrent** turns GH Archive's hourly GitHub event files (`https://data.gharchive.org/YYYY-MM-DD-H.json.gz`) into a canonical, deduplicated event table and metrics, and proves the result correct. Owner: **Steven**. He approves every spec change and every merge.

**How correctness is proved:**
- Two implementations of the same spec are written by different agents, who never read each other's code. Their outputs must be **exactly** equal.
- A third agent writes test fixtures by hand from the spec.
- Gate 1 (September 2026) **passed**, with evidence generated in CI: `evidence/gate1.json`.
- Current work is live ingestion (`02-live-ingestion.md`), toward Gate 2.

## Authority (in order)

1. `01-event-semantics.md`: event semantics, quarantine, dedup, time, output contract, Gate 1.
2. `02-live-ingestion.md`: fetcher, `available_at` manifest, delay measurement, Gate 2.
3. `fixtures/SPEC-GAPS.md`: every gap the spec missed, and its decision (G1–G33).
4. Your brief in `briefs/`.

If code and spec disagree, **the code is wrong**. If the spec is silent:
- add the next `G` number to `fixtures/SPEC-GAPS.md`, marked OPEN
- state your provisional choice
- tell Steven

Never resolve a gap by looking at how the other implementation does it.

## Roles and where each one works

| Role | Writes | Never reads | Checkout | Branch |
|---|---|---|---|---|
| Reference author and scrum master (Claude, main session) | `reference/`, `tools/`, specs (Steven approves), `briefs/`, `README.md`, `BENCHMARKS.md` | `pipeline/` | `~/Documents/undercurrent/undercurrent` | short topic branches |
| Pipeline author (Claude, separate session) | `pipeline/` | `reference/`, `changes/*-reference-*.md` | `~/Documents/undercurrent-pipeline` (sparse-checkout hides `reference/`) | `pipeline` |
| Verifier (Copilot) | `fixtures/` only | `pipeline/`, `reference/`, `changes/*-reference-*.md` | `~/undercurrent-verifier` | `verifier-*` |
| Helper (any agent, no brief) | docs, notes, answers | must not carry knowledge between `pipeline/` and `reference/` | wherever Steven opens it | — |

- **Report to the scrum master** (the main-repo Claude session; find its current name with ListAgents, or go via Steven), including spec gaps. What it may do is under Autonomy below.
- **Work only in your own checkout and on your own branch.** Never commit into another agent's checkout.
- If your role isn't clear, ask.
- Shared, neutral code (`tools/`) imports neither implementation.

## Layout

| Path | What |
|---|---|
| `01-event-semantics.md`, `02-live-ingestion.md` | the specs |
| `fixtures/Fxx-*/` | one test case each: `input/*.json.gz`, `fixture.json`, `expected/*.csv`, `README.md`, optional `available_at.csv` |
| `fixtures/README.md` | fixture index and conventions. Read it instead of opening every fixture. |
| `fixtures/generate_inputs.py` | writes every `input/*.json.gz` from literal lines. It must stay byte-identical for existing fixtures. |
| `fixtures/event_types.txt` | the 16 recognized event types (01 §2) |
| `pipeline/` | the product (`python -m pipeline`) |
| `reference/reference.py` | the independent check (~350-line limit, 01 §6) |
| `tools/compare_outputs.py` | exact comparison of R1–R7 CSVs |
| `tools/reconcile.py`, `tools/bigquery/` | reconciliation against BigQuery (01 §5.2) |
| `tools/archive_input.py` | builds a flat input folder from a live fetcher root, using each hour's final fetch-log outcome (02 §6, §8.4) |
| `tools/delay_report.py` | the delay report from a live fetcher root: counts, delay percentiles, proposed `L` (02 §7) |
| `tools/gate1.sh`, `tools/gate1_evidence.py`, `tools/gate1_config.json` | the Gate 1 run (CI only) |
| `tools/test_*.py` | tests for the tools; `test_manifest_errors.py` runs both implementations black-box |
| `check.sh` | every repeatable check, in one command |
| `.github/workflows/` | `check.yml` (every push), `gate1.yml` (manual, self-hosted runner) |
| `evidence/` | Gate 1 evidence; reconciliation categories |
| `briefs/` | task briefs per agent |
| `changes/` | one note per change; the index is `changes/README.md` |
| `BENCHMARKS.md` | every measured number |

## Commands

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt     # once (Python 3.13, DuckDB)
./check.sh                                                             # everything; exit 0 = pass
.venv/bin/python -m pipeline fixtures fixtures OUT                     # pipeline on every fixture
.venv/bin/python reference/reference.py fixtures fixtures OUT          # reference on every fixture
.venv/bin/python tools/compare_outputs.py fixtures fixtures OUT        # compare against expected/
.venv/bin/python tools/compare_outputs.py dirs A B                     # compare two output dirs
python3 fixtures/generate_inputs.py                                    # regenerate fixture inputs
```

Both implementations: `run INPUT_DIR FIRST_HOUR LAST_HOUR OUT_DIR [--cutoff T ...] [--available-at FILE]`, with hours like `2026-09-01T00:00:00Z`, inclusive.

## Facts agents get wrong

- **Output files** (01 §6): `r1.csv r2.csv r3.csv r4.csv r5.csv registry.csv flags.csv`.
  - LF line endings, RFC 4180 quoting.
  - Rows are compared as exact text after sorting, so `7` ≠ `07`.
  - `registry_evidence.csv` and `canon_digest.csv` are extra files and are not compared.
- **`fixture.json`:** `{"id","title","requested_hours":[first,last],"cutoffs":[...]}`. `requested_hours` is **always a 2-element inclusive pair**; one hour is `[h, h]`.
- **Expected outputs are derived by hand from the spec.** Never copy them from running an implementation, and never edit one to make a test pass.
- **File names:** an hour is not zero-padded (`2026-09-01-5.json.gz`).
- **Timestamps:** UTC, `YYYY-MM-DDTHH:MM:SSZ` in outputs.
- **Truncated gzip:** reading with `gzip.open` loses the last partial line; see 01 §1.
- **`available_at` manifest** (02 §8): the header is exactly `source_file_hour,available_at`. Values need an explicit offset and at most 6 fractional digits. A repeated hour is an error. Unlisted hours use the backfill rule `h + 1h + 6h`.
- **Data lives outside the repo**, in `~/undercurrent-data/` (`gharchive/` inputs at 19 GB, `runs/` outputs). Never commit it, and don't open it to "look around".
- **iCloud:** `~/Documents` is iCloud-synced and creates `name 2.ext` duplicates. They are git-ignored; never commit or edit them.

## Autonomy: what agents start without asking Steven

Roles: **Steven** is the project manager (decisions, merges, money). The **scrum master** is the main-repo Claude session (`~/Documents/undercurrent`); it runs routine testing and review between agents and owns code quality and refactoring. The **developers** are the pipeline Claude session and Copilot (verifier).

**Any agent may, without asking:**
- push its own branch (never `main`) and open or update a PR from it
- request a PR review from Copilot (`gh pr edit N --add-reviewer @copilot`), or run a reviewer headless in its own checkout (`copilot -p`, `codex exec`)
- ask Gemini for a second opinion on a choice that is not a spec decision (`gemini -p`)
- ask another Claude session to run a check and report the result (SendMessage)
- ask the verifier for fixtures that cover a spec section

**Steven only:**
- spec changes, and deciding any `G` gap (agents still open gaps as OPEN, with a provisional choice)
- merges to `main`
- anything that costs money or changes the cloud account; destructive actions on the fetcher VM (stop, delete, wiping the archive)
- starting or restarting a Gate window
- a refactor that is **too messy for the scrum master to fix in passing** (see below)

**Messages between agents (independence, 01 §6).** A request names only spec sections, fixture IDs, commands, file paths, and pass/fail results. It never contains code, pseudo-code, or how either implementation works. Between `pipeline/` and `reference/` this holds in both directions, and nobody carries such knowledge between them. The scrum master is also the reference author, so it never reads `pipeline/`: code review of `pipeline/` goes to a helper that never touches `reference/` (e.g. a headless `codex exec` or `gemini -p` run in the pipeline checkout), not to Copilot, which as verifier never reads `pipeline/` either. The scrum master acts on the helper's findings (issue list, not code).

**Refactoring and code quality (the scrum master).**
- Has every agent's PR reviewed for the house style: the simplest code that meets the spec, names and comments matching the surrounding code, no dead code, tests beside the code, a change note per change.
- Small issues: fixed in passing by whoever owns the file, or sent back to the author as a review comment.
- Too messy (a module that needs restructuring, duplicated logic across files, a design that fights the spec): the scrum master writes `changes/YYYY-MM-DD-refactor-<topic>.md` (what, why, proposed shape, risk) and stops for Steven, who sends out the work.

**When to coordinate.** At the end of a brief step, when a gap opens, or when a PR is ready. Not on every commit: each headless run starts cold and costs tokens.

## Working rules (Steven's)

- **Every change gets its own note** in `changes/YYYY-MM-DD-<topic>.md`: why, what changed, proof (commands and results), and what is still open. Add a line to `changes/README.md`.
- **Every measurement goes in `BENCHMARKS.md`**, following the rules at its top. Say whether the machine was idle. Mark estimates as estimates. These numbers support resume claims, so they must be exact.
- **No over-coding.** Write the simplest thing that meets the spec. Tidy what you touch without changing behaviour, and put bigger refactors in a separate write-up.
- **Run `./check.sh` before saying anything is done,** and quote its result.
- **Commit locally on your branch; Steven pushes and merges.** Don't push unless he asks.
- **Keep reports short:** 10 lines or fewer. Stop at the end of each brief step.

## Saving tokens

Read only what your task needs, in this order: this file → your brief → the spec sections it names → `fixtures/README.md`. Don't open fixture inputs, `.venv/`, `evidence/gate1.json` (720 hashes) or `~/undercurrent-data/`.

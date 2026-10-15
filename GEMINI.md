# undercurrent: instructions for Gemini

A verified GH Archive event pipeline. Correctness is checked by comparing it against an independent reference calculation, so **who reads what matters more than usual**. Owner: Steven.

## Authority

`01-event-semantics.md` is the spec, and it is authoritative. If code and spec disagree, the code is wrong. You may **propose** spec edits; only Steven approves them (§10). Once he approves, bump the version and record the decision in §9 and `fixtures/SPEC-GAPS.md`.

## Your role: check before starting

Each session has exactly one role. Your task brief says which one. If it doesn't, ask.

| Role | Brief | You write | You never write |
|---|---|---|---|
| Verifier (§7) | `briefs/verifier-F18-plus.md` | `fixtures/` | pipeline or reference code |
| Pipeline author (§6) | `briefs/pipeline-author.md` | `pipeline/` | fixtures' expected outputs, reference code |

Under §7 the verifier does not author pipeline code. Don't take the pipeline role in a project where you have written fixtures unless Steven explicitly assigns it.

## Independence (hard rules)

- Never read `reference/` or the change notes listed in `.geminiignore`, including through shell commands (`cat`, `grep`, `git show`, `git log -p`). `.geminiignore` only hides these from file tools. Not reading them is up to you.
- You may **run** `./check.sh`, which runs the reference. Never change an expected output or pipeline behaviour to make it agree with the reference. Report the mismatch to Steven with your derivation from the spec.
- If the spec is silent, don't guess silently. Add the next `G` number to `fixtures/SPEC-GAPS.md`, mark it OPEN, and state the provisional behaviour.

## Layout

| Path | What |
|---|---|
| `01-event-semantics.md` | spec |
| `fixtures/README.md` | fixture index (F01–F27), CSV conventions. Read this instead of opening every fixture. |
| `fixtures/SPEC-GAPS.md` | every spec gap and its decision |
| `fixtures/generate_inputs.py` | writes every `input/*.json.gz` from literal lines |
| `tools/compare_outputs.py` | exact-equality comparator (shared, stdlib only) |
| `check.sh` | comparator tests → reference on fixtures → comparison |
| `changes/` | one note per change |
| `briefs/` | task briefs |

## Commands

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
./check.sh                               # exit 0 = everything passes
python3 fixtures/generate_inputs.py      # regenerate inputs; must be byte-identical for existing fixtures
```

## Working rules (Steven)

- **Every change gets its own note** in `changes/YYYY-MM-DD-<topic>.md`: why, what changed, proof (commands and results), and anything left open.
- **No over-coding.** Write the simplest thing that meets the spec. Tidy files you touch without changing behaviour. Flag bigger messes in a separate refactor write-up instead of fixing them on the side.
- **Commit locally; never push.** Steven reviews, then pushes.
- **Record every measurement in `BENCHMARKS.md`** (timings, memory, sizes, row counts, fixture results, bugs found), one row each, following the rules at the top of that file. Mark estimates as estimates. These numbers back resume claims, so they must be exact and reproducible.
- Run `./check.sh` before saying anything is done, and quote its result.

## Keep requests low (the quota is small)

- Read only the files your brief names. Use `fixtures/README.md` and the per-fixture `README.md` instead of opening every CSV.
- Do one brief section per session, then stop and summarise.
- Batch edits into one file write where you can, instead of many small edits.

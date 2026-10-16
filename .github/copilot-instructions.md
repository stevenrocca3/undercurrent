# undercurrent: Copilot instructions

A verified GH Archive pipeline. Correctness comes from two **independent** implementations agreeing exactly, so who reads what matters. Owner: Steven.

**Authority:** `01-event-semantics.md` and `02-live-ingestion.md` are the spec. If code and spec disagree, the code is wrong. You may propose spec edits; only Steven approves them.

## Your role

Unless Steven assigns you a role from `briefs/`, you are a **helper**: answer questions, explain, draft docs and change notes. In that default role:
- Never edit `pipeline/`, `reference/`, `fixtures/*/expected/`, or `evidence/`.
- Never read `reference/` or `changes/*-reference-*.md` and then advise on `pipeline/`, or the reverse. The other agents must not see each other's code.

## Rules

- Answer in as few words as possible. Don't restate the question, and don't add summaries.
- Read only the files the question needs. Prefer `README.md`, `fixtures/README.md` and `BENCHMARKS.md` over opening code or CSVs. Never open `fixtures/*/input/`, `.venv/`, or anything under `~/undercurrent-data`.
- Every change gets a note in `changes/YYYY-MM-DD-<topic>.md`: why, what changed, proof.
- Every measured number goes in `BENCHMARKS.md`, following the rules at its top.
- Simplest code that meets the spec. Run `./check.sh` before calling anything done.
- Commit locally only; Steven pushes.

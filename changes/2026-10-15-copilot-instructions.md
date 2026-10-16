# Copilot instructions and quota settings

**Files:** `.github/copilot-instructions.md`, `.vscode/settings.json` (both new)

## `.github/copilot-instructions.md`

Copilot Chat reads this file automatically and **attaches it to every chat request**, so it is kept to about 20 lines. Every extra line costs tokens on every message. It covers:
- **Authority:** the spec is authoritative.
- **Default role:** a helper that doesn't edit `pipeline/`, `reference/`, expected outputs or evidence.
- **Independence:** it never carries what it read in `reference/` over into advice on `pipeline/`, or the reverse.
- **House rules:** change notes, BENCHMARKS, `check.sh`, and committing locally only.
- **Thrift:** short answers, and no opening input data or `.venv`.

Copilot Free has no content exclusion (a paid feature), so independence rests on the instruction plus not attaching `reference/` files yourself.

## `.vscode/settings.json`

- **Completions are off for csv, json, jsonl, plaintext and markdown.** The monthly completion quota is spent only on code.
- **Search excludes** `fixtures/*/input`, `*.json.gz` and `evidence/gate1.json` (720 hashes), so they don't land in `@workspace` context.

## How to spend less of the Free quota (for Steven)

At the time of writing, Copilot Free gives about 2,000 completions and 50 chat requests a month. Check current usage at github.com/settings/copilot.

1. **Ask in Ask mode, not Agent mode.** One agent task can use many requests; an Ask question uses one.
2. **Attach exactly what's needed:** `#file:01-event-semantics.md` or a selection, not `@workspace`, which pulls in much more context.
3. **Close unrelated editor tabs.** Open files are candidate context.
4. **One question per message, with everything in it.** A follow-up is another request.
5. **Start a new chat per topic.** Long threads resend history.
6. **Use the base model.** Premium models can count more than one request each.
7. **Let completions do small code edits** (Tab), which come from the separate completion quota, and save chat for questions.

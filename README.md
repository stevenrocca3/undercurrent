# undercurrent

Spec: `01-event-semantics.md`. Change notes: `changes/`.

## Checks

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
./check.sh
```

`check.sh` runs the comparator tests, the reference on every fixture, and the comparison against `fixtures/*/expected/`. Exit 0 = all pass. Set `PYTHON` to use a different interpreter (e.g. in CI).

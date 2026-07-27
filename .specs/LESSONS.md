# LESSONS — auto-maintained by scripts/lessons.py

> Machine-owned. Do NOT hand-edit. Changes are overwritten on the next `lessons.py` write.
> Canonical state lives in `.specs/lessons.json`. Edit lessons only via the script.
> promote_threshold=2 distinct features · window_days=45 · quarantine_threshold=2

## Confirmed (load these at Specify/Design)

Corroborated across multiple features. Safe to apply as guidance.

_none_

## Candidates (under observation — do NOT load as guidance yet)

Seen once or not yet corroborated. Tracked, not trusted.

### L-001 — Use timezone-aware datetime/date constructors consistently across a whole diff (datetime.now(UTC), date.fromisoformat) - a single leftover naive datetime.strptime or date.today() call trips ruff DTZ rules and fails the mandatory Build gate.
- signal: `gate_fail` · recurrence: 1 feature(s) · scope: `date-handling` · harmful: 0
- features: ingestao-curadoria
- evidence: app/aggregation/indicators.py:59-60,scripts/generate_fixture.py:62 (date-handling)
- last seen: 2026-07-27T02:07:07Z

### L-002 — When a spec-required review/audit queue is implemented as in-memory-only state, treat it as unresolved until a persistence decision is made, since in-memory state does not survive process restarts or become visible to downstream consumers.
- signal: `spec_deviation` · recurrence: 1 feature(s) · scope: `versioning` · harmful: 0
- features: ingestao-curadoria
- evidence: SPEC_DEVIATION (T11) tasks.md / app/curation/treated_layer.py:32 (versioning)
- last seen: 2026-07-27T02:07:11Z

### L-003 — When a calculation formula branches on a domain value not yet confirmed by the real data source, add a test case that forces the ambiguous branch to diverge from the default path, so the documented assumption is provably implemented and not just described in a comment.
- signal: `spec_deviation` · recurrence: 1 feature(s) · scope: `aggregation` · harmful: 0
- features: ingestao-curadoria
- evidence: SPEC_DEVIATION (T12/T13) tasks.md / app/aggregation/indicators.py:1-18 (aggregation)
- last seen: 2026-07-27T02:07:15Z

### L-004 — When an edge case has a unit test at the domain layer, add the equivalent integration/route-level test too, since unit coverage does not guarantee the HTTP layer wires the same error path correctly.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `ingestion` · harmful: 0
- features: ingestao-curadoria
- evidence: tests/integration/test_ingestion_endpoint.py (missing corrupted-CSV case) (ingestion)
- last seen: 2026-07-27T02:07:37Z

## Quarantined (failed when applied — ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_

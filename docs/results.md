# Experimental Results

**Author:** Rodrigue Lecomte
**Last updated:** 2026-03-07

This document tracks findings across simulation runs. Each run produces a local
`run_metadata.json` with full parameters and context; this page curates the
big-picture observations that emerge across runs.

---

## Run Log

| # | Date | Seed | Agents | Rate | Curve | API Calls | Verdicts | Notes |
|---|------|------|--------|------|-------|-----------|----------|-------|
| 1 | 2026-03-06 | 42 | 5 | 100 | exponential | 745 | 5 COLLAPSE, 2 NOVEL_MECHANISM | Prompt rule 3 biased toward collapse — fixed after this run |
| 2 | 2026-03-07 | 42 | 5 | 100 | exponential | 747 | 6 COLLAPSE, 1 PERSIST_ACTIVE (employment) | Post-fix run; employment never collapses |

Both runs used `grok-4-1-fast-reasoning`, pilot-scale parameters (20/100/20/10 phase durations).

---

## Emerging Patterns

### Employment persists stubbornly
Across both runs, employment is the only mechanism that survives the transition to
post-scarcity. It maintains full adoption (1.0) and high behavioral pattern similarity
to baseline (BPS 0.925). This is the strongest signal so far — either employment
coordinates something agents perceive as inherently scarce (time, effort, purpose),
or the prompt encodes assumptions about work that resist the scarcity parameter.

### No REPURPOSE observed at pilot scale
Zero mechanisms have repurposed across two runs. All non-employment mechanisms
collapse cleanly rather than shifting to coordinate different goods. This may be a
scale effect (5 agents produce limited counterparty interactions) or a genuine finding.
The full sweep (Phase 3, 100 agents) will clarify.

### Zero custom actions
Agents stay within the predefined action vocabulary. No emergent coordination
mechanisms have appeared. Worth monitoring — this could change with more agents
and slower transitions.

### No replacement chains
When mechanisms collapse, nothing fills the gap. The retroanalysis tracer finds no
replacement patterns. Employment handles everything alone.

---

## Open Questions

- Does REPURPOSE emerge with more agents (100) or slower transition rates (5, 25)?
- Is employment persistence a prompt artifact or a genuine finding about labor coordination?
- Will custom actions appear with richer agent interactions at full scale?
- Do different scarcity curves (linear, step) produce qualitatively different outcomes?

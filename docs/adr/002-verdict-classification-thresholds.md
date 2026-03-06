# ADR-002: Verdict Classification Thresholds

**Status:** accepted
**Date:** 2026-03-06

## Context

After a simulation run completes all five phases (baseline, transition, steady-state, reversibility, retroanalysis), each of the 7 coordination mechanisms receives a verdict classifying its fate. The verdict decision tree requires several numeric thresholds and qualitative criteria that are not self-evident from the research hypotheses. These thresholds determine the boundary between, e.g., a mechanism that "collapsed" versus one that went "dormant," or one that "persisted" versus one that was "repurposed." Wrong thresholds produce misleading verdicts. The pilot run (5 agents, 50 cycles, seed 42) provides initial calibration data but is too small for final tuning — thresholds must be defensible yet adjustable before the production sweep.

## Decision

### Threshold definitions

| Parameter | Value | Where defined |
|-----------|-------|---------------|
| `collapse_threshold` | 0.05 | `SimConfig` (existing) |
| `collapse_sustained_n` | 20 | `SimConfig` (existing) |
| `efficiency_idle_band` | [0.9, 1.1] | New in SimConfig |
| `behavioral_pattern_threshold` | 0.6 | New in SimConfig |
| `recovery_adoption_threshold` | 0.10 | New in SimConfig |
| `recovery_sustained_n` | 10 | New in SimConfig |

### Full decision tree with precise definitions

**Step 1 — Collapse check (Phase 3: steady-state)**

A mechanism receives `COLLAPSE` candidacy if its `adoption_rate < 0.05` for 20 consecutive cycles anywhere in Phase 3. "Consecutive" means unbroken — a single cycle at or above 0.05 resets the counter.

If collapse candidacy is met, check Phase 4 (reversibility):
- **Recovery** = `adoption_rate >= 0.10` for at least 10 consecutive cycles during Phase 4.
- If recovery: verdict = `PERSIST_DORMANT` (mechanism was latent, not dead).
- If no recovery: verdict = `COLLAPSE` (irreversible disappearance).

Recovery threshold (0.10) is deliberately higher than collapse threshold (0.05) to avoid classifying noise as recovery. The recovery window (10 cycles) is shorter than collapse window (20) because Phase 4 is only 50 cycles — requiring 20 would consume 40% of the phase and miss late recoveries.

**Step 2 — Idle check**

If the mechanism did not collapse: check `coordination_efficiency`.

"Approximately 1.0" is defined as the closed interval [0.9, 1.1]. This means the mechanism's entropy ratio (implemented in Phase 2) is within 10% of the baseline value. If `coordination_efficiency` falls within [0.9, 1.1] and `adoption_rate >= 0.05`:
- Verdict = `PERSIST_IDLE` (mechanism still used but doing the same work as under scarcity).

**Step 3 — Active/Repurpose/Novel classification**

If `coordination_efficiency > 1.1` (mechanism is doing more coordination work than baseline):

- Compute `behavioral_pattern_score` (BPS) — cosine similarity between the mechanism's current action-type distribution and its Phase 1 baseline distribution. Already implemented in `collector.py` via `_cosine_similarity()`.

- **BPS >= 0.6 AND goods_domain != baseline**: the mechanism is being used in a recognizably similar way but applied to different goods. Run the information structure check (Step 4).

- **BPS >= 0.6 AND goods_domain == baseline**: mechanism persists in its original role with enhanced efficiency. Verdict = `PERSIST_ACTIVE`.

- **BPS < 0.6**: the mechanism's action-type distribution has shifted so far from baseline that it is functionally a different mechanism. Verdict = `NOVEL_MECHANISM`.

The 0.6 threshold means at least 60% cosine similarity to baseline patterns. Below 0.6 indicates the action-type mix has substantially changed (e.g., "price" actions dominated by "bid/ask" in baseline but now dominated by "accept_price" in post-scarcity).

**Step 4 — Information structure check**

When BPS >= 0.6 and goods_domain has shifted, determine whether the mechanism is repurposed or truly novel by examining what coordination problem it solves:

- **Discovery process**: the mechanism helps agents find or match with counterparties or goods they could not locate otherwise. Operationalized as: the mechanism's actions disproportionately involve goods that were not in the agent's initial resource endowment and were not present in Phase 1 actions for that agent. Verdict = `REPURPOSE`.

- **Labeling process**: the mechanism creates new categories, signals, or distinctions that did not exist in the baseline vocabulary. Operationalized as: >30% of the mechanism's action `details` fields contain target_good values absent from the Phase 1 goods list. Verdict = `NOVEL_MECHANISM`.

If neither criterion is met clearly, default to `REPURPOSE` (conservative — assumes the mechanism found a new use rather than became something new).

**Step 5 — Goods domain comparison**

`goods_domain == baseline` is true when the set of `target_good` values for a mechanism in Phase 3 has Jaccard similarity >= 0.7 with its Phase 1 target_good set. Below 0.7 = domain has shifted.

### Summary table

| Verdict | Condition |
|---------|-----------|
| `COLLAPSE` | adoption < 0.05 for 20 consecutive cycles in Phase 3, no recovery in Phase 4 |
| `PERSIST_DORMANT` | Same collapse trigger, but recovers (adoption >= 0.10 for 10 cycles) in Phase 4 |
| `PERSIST_IDLE` | No collapse, efficiency in [0.9, 1.1] |
| `PERSIST_ACTIVE` | No collapse, efficiency > 1.1, BPS >= 0.6, same goods domain |
| `REPURPOSE` | No collapse, efficiency > 1.1, BPS >= 0.6, different goods domain, discovery process |
| `NOVEL_MECHANISM` | No collapse, efficiency > 1.1, BPS < 0.6 OR (BPS >= 0.6, different domain, labeling process) |

## Rationale

- **collapse_threshold = 0.05**: With 100 agents, 0.05 means fewer than 5 agents used the mechanism. Below this, the signal is indistinguishable from random noise. The pilot showed mechanisms fluctuating at 0.2-1.0 when active — 0.05 is well below any "alive" mechanism observed.
- **collapse_sustained_n = 20**: A single-cycle dip to 0 is not a collapse — it could be scheduling noise. 20 cycles is 10% of Phase 3 (200 cycles), long enough to distinguish structural abandonment from fluctuation.
- **efficiency_idle_band [0.9, 1.1]**: 10% tolerance accounts for stochastic variation in the entropy ratio. Tighter bands (e.g., +/-5%) would misclassify natural variance as meaningful change. Wider bands (e.g., +/-25%) would hide genuine shifts.
- **behavioral_pattern_threshold = 0.6**: Cosine similarity of 0.6 means the action-type vectors share roughly 60% of their directional alignment. Below this, the mechanism's behavioral fingerprint has changed enough to question whether it is the "same" mechanism. This is a standard threshold in information retrieval for "similar but not identical."
- **recovery thresholds (0.10, 10 cycles)**: Asymmetric with collapse by design. Recovery should clear a higher bar than mere noise to be classified as dormancy rather than collapse. 10 cycles is 20% of Phase 4 (50 cycles) — long enough to be intentional.
- **goods_domain Jaccard >= 0.7**: Standard threshold for set similarity. Below 0.7, the mechanism is operating on a substantially different set of goods.

### Calibration approach

1. **Pilot calibration** (current): thresholds set from first principles and pilot observations. The pilot showed employment at 0.2-1.0 adoption across all phases — well above collapse_threshold. Property dropped but did not sustain below 0.05. These observations confirm the thresholds are not obviously wrong.
2. **Pre-production validation**: run 3-5 seeds at production scale (100 agents, 450 cycles) with the current thresholds. Inspect edge cases where verdicts seem wrong. Adjust thresholds if needed.
3. **Sensitivity analysis** (Phase 3): after the full sweep, re-run verdict classification with +/-20% threshold perturbations to confirm verdicts are stable. Report any mechanisms whose verdict flips under perturbation — these are the interesting cases for the paper.

All thresholds are defined in `SimConfig` so they are recorded in every run's metadata and reproducible. No threshold is hardcoded in classification logic.

## Consequences

- Adding 4 new fields to `SimConfig` increases its surface area, but all are verdict-related and logically grouped. The dataclass remains the single source of truth.
- `coordination_efficiency` is still a placeholder (1.0) per ADR-001. Until Phase 2 implements the entropy ratio, the idle/active/repurpose branches of the tree are inert — every non-collapsed mechanism will fall into `PERSIST_IDLE` (since 1.0 is within [0.9, 1.1]). This is acceptable: Phase 1 only needs to validate the collapse/dormant branch.
- The information structure check (Step 4) relies on `details` field content from LLM responses, which is free-text. Classification quality depends on the LLM producing consistent `target_good` values — monitored via the `novel_actions.csv` export.
- Sensitivity analysis adds computational cost (re-running classification ~10 times per sweep) but classification is pure pandas — negligible compared to the LLM API cost of the sweep itself.

## See Also
- ADR-001: AgentReasoner prompt structure (defines the response schema that feeds these metrics)

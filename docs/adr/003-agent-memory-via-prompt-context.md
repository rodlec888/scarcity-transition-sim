# ADR-003: Agent Memory via Prompt Context

**Date:** 2026-03-07

## Context

Agents currently receive their last 5 raw actions as "recent history" but have no
narrative memory — no awareness of their own behavioral patterns, what mechanisms
they've abandoned, or how their strategy has shifted as scarcity changed. This lack
of continuity likely prevents REPURPOSE behavior: an agent cannot redirect a mechanism
to coordinate different goods if it has no memory of having used that mechanism before
or why it stopped.

Two pilot runs (5 agents each) produced zero REPURPOSE verdicts and zero custom actions.
Employment persists while all other mechanisms collapse cleanly. The agents lack the
self-awareness needed to adapt rather than simply react to current state.

## Decision

Add a structured behavioral summary to the user prompt, computed from the agent's
full `action_history`. The summary provides self-reflection context without requiring
additional API calls or persistent memory storage beyond what already exists.

The summary includes:
1. **Mechanism usage distribution** over a rolling window (last 20 cycles)
2. **Abandoned mechanisms** — mechanisms the agent used earlier but stopped using,
   with the scarcity level at last use
3. **Scarcity trajectory** — scarcity when the agent's history begins vs. current
4. **Recent action log** — last 5 actions (already exists, retained)

## Rationale

- The data already exists in `action_history` — no new storage or API calls needed
- A computed summary is more useful than raw logs; agents can reason about patterns
- The rolling window (20 cycles) balances memory depth against prompt size (~150-200 tokens)
- Abandoned mechanism tracking directly enables the "I used to use X, maybe I can
  repurpose it" reasoning path
- Scarcity-at-last-use context lets agents connect mechanism abandonment to environmental change

## Consequences

- Prompt input tokens increase by ~150-200 per call (negligible cost impact at current rates)
- Agent behavior may change — this is intentional and the reason for landing this
  before the 20-agent scale-up rather than after
- Previous pilot results are not directly comparable to post-ADR-003 runs (different
  prompt = different experiment). This is documented in `docs/results.md`.
- The summary computation is deterministic (derived from history) — no new randomness introduced

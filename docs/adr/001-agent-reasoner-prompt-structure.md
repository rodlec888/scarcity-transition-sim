# ADR-001: AgentReasoner prompt structure and action parsing contract
**Date:** 2026-03-04

## Context
The AgentReasoner is the only class that communicates with the xAI API. Its prompt structure and response parsing define the boundary between LLM reasoning and Mesa scheduling. Getting this contract wrong means either losing emergent behavior (too constrained) or losing measurability (too free-form).

## Decision
Two-message prompt architecture with JSON-only structured response.

**System prompt** (static, identical for all agents across all cycles):
- Defines the agent's role in the simulation
- Lists the full structured action vocabulary (7 mechanisms + custom)
- Specifies the exact JSON response schema: `{mechanism, action_type, target_good, counterparty, reasoning, details}`
- Explicitly instructs JSON-only output

**User prompt** (dynamic, per-agent per-cycle):
- Current cycle number and phase name
- Material scarcity level (0.0-1.0)
- Agent persona description (natural language from `Persona.describe()`)
- All goods with their scarcity levels
- Neighbor IDs and their recent actions (capped at 10 for prompt size)
- Agent's own recent actions (last 5 cycles)

**Response parsing contract:**
- Parse JSON from response (strip markdown code fences if present)
- Validate `mechanism` against known vocabulary — unknown falls back to `custom`
- Validate `action_type` belongs to the declared mechanism — mismatch falls back to `custom`
- Any `custom` action is recorded with its reasoning for retroanalysis
- Parse failures return `None` (agent takes no action that cycle)

## Rationale
- JSON-only response avoids regex parsing of free-form text — deterministic extraction
- The `custom` escape hatch preserves the emergent behavior space required by the research design
- Fallback-to-custom on parse errors means malformed responses still produce signal rather than lost data
- Static system prompt + dynamic user prompt keeps token count predictable (~500 input tokens per call)
- Persona as natural language rather than raw floats gives the LLM richer context for reasoning

## Consequences
- Temperature 0.7 introduces stochastic variation per call — acceptable for this research, but means exact replay requires API-level response caching (not implemented in Phase 1)
- The `reasoning` field is free-text and not used in Mesa scheduling — it exists only for retroanalysis and debugging
- `coordination_efficiency` is a placeholder (1.0) in Phase 1 — requires Phase 2 implementation to compute entropy ratios
- Synchronous API calls (one per agent per cycle) are acceptable for pilot but must migrate to Batch API for production sweeps

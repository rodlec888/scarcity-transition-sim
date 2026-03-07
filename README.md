# scarcity-transition-sim

Parametric agent-based simulation studying what happens to economic coordination
mechanisms when AI drives material scarcity toward zero.

Seven mechanisms are tested: **price signals, money, property rights, employment,
taxation, reputation, and queuing**. Each is tracked through a 5-phase protocol
that measures whether it collapses, persists through inertia, or repurposes itself
to coordinate goods that remain scarce (attention, status, location, time).

Built with [Mesa 3](https://mesa.readthedocs.io/). Agents reason via LLM
(xAI API) — each agent receives the current economic state and chooses which
coordination mechanism to use, producing structured actions that feed back into
the simulation.

## Research question

> Do coordination mechanisms designed for scarcity collapse, persist through
> inertia, or repurpose themselves when material scarcity ends?

## How it works

Each run follows a **5-phase protocol**:

1. **Baseline** — Full scarcity. All 7 mechanisms active. Establishes reference behavior.
2. **Transition** — Scarcity drops from 1.0 to 0.0 along a parametric curve (linear, exponential, or step). Track how mechanisms respond.
3. **Steady state** — Post-scarcity plateau. Measure sustained adoption and coordination efficiency.
4. **Reversibility probe** — Re-inject partial scarcity. Mechanisms that recover were dormant, not dead.
5. **Retroanalysis** — Classify each mechanism's fate and trace functional replacement chains.

Each mechanism receives one of six **verdicts**: `COLLAPSE`, `PERSIST_DORMANT`,
`PERSIST_IDLE`, `PERSIST_ACTIVE`, `REPURPOSE`, or `NOVEL_MECHANISM`.

## Status

This project is under active research. The simulation pipeline is validated and
producing results. A full parameter sweep and paper are upcoming.

**Current findings** are tracked in [Experimental Results](docs/results.md) — early
runs show employment persisting stubbornly while all other mechanisms collapse at
pilot scale.

## Quick start

```bash
# Install dependencies
uv sync --all-extras

# Copy environment template and add your xAI API key
cp .env.example .env

# Run tests (213 tests, zero API calls, ~2s)
make test

# Run a single experiment
uv run python scripts/run_single.py \
    --transition-rate 100 --curve exponential --seed 42 \
    --n-agents 5 --phase1-cycles 20 --phase3-cycles 20 --phase4-cycles 10
```

## Outputs

Each run writes to a timestamped folder under `outputs/` (never overwritten):

| File | Contents |
|------|----------|
| `run_metadata.json` | Full parameters, model version, timing, verdicts — the lab notebook |
| `cycle_data.csv` | Per-mechanism metrics every cycle (adoption rate, coordination efficiency, behavioral pattern score) |
| `run_summary.csv` | One row per mechanism with its final verdict |
| `novel_actions.csv` | Free-text log of any emergent (`custom`) actions |
| `agent_actions.csv` | Every individual LLM decision — mechanism, action type, target good, reasoning, persona |

## Parameter space

`4 transition_rates x 3 scarcity_curves x 3 seeds = 36 runs` (full sweep)

| Parameter | Values |
|-----------|--------|
| `transition_rate` | 5, 25, 100, 500 cycles |
| `scarcity_curve` | linear, exponential, step |
| `random_seed` | 3 seeds per combination |

## Documentation

- [Theoretical Framework and Research Hypotheses](docs/research.md)
- [Simulation Architecture](docs/architecture.md)
- [Experimental Results](docs/results.md)
- [ADR-001: Agent Reasoner Prompt Structure](docs/adr/001-agent-reasoner-prompt-structure.md)
- [ADR-002: Verdict Classification Thresholds](docs/adr/002-verdict-classification-thresholds.md)

## Stack

Python 3.11+ · Mesa 3 · xAI API · pandas · uv

## License

MIT — see [LICENSE](LICENSE).

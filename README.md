# scarcity-transition-sim

Parametric agent-based simulation studying what happens to economic coordination
mechanisms — price signals, money, property rights, employment, taxation,
reputation, and queuing — when AI drives material scarcity toward zero.

Built with [Mesa 3](https://mesa.readthedocs.io/) and LLM-powered agents via the xAI API.

## Research question

Do coordination mechanisms designed for scarcity collapse, persist through inertia,
or repurpose themselves to coordinate the goods that remain scarce (attention, status,
location, time) when material scarcity ends?

## Documentation

- [Theoretical Framework and Research Hypotheses](docs/research.md)
- [Simulation Architecture](docs/architecture.md)

## Quick start

```bash
# Install dependencies
uv sync --all-extras

# Copy environment template and add your xAI API key
cp .env.example .env

# Run pilot (5–10 agents, single seed — validates the pipeline)
make pilot

# Run full parameter sweep (100 agents, 36 runs)
make sweep
```

## Parameter sweep

`4 transition_rates × 3 scarcity_curves × 3 seeds = 36 runs`

| Parameter | Values |
|-----------|--------|
| `transition_rate` | 5, 25, 100, 500 cycles |
| `scarcity_curve` | linear, exponential, step |
| `random_seed` | 3 seeds per combination |

## Stack

Python 3.11+ · Mesa 3 · xAI API · pandas · uv

## License

MIT — see [LICENSE](LICENSE).

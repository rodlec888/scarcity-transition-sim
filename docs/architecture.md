# Simulation Architecture

**Version:** v0.1 — Pre-simulation draft
**Last updated:** 2026-03-08

---

## Run Protocol

The simulation is a 5-phase sequence. Each phase has a defined purpose and measurement objective.

```
┌─────────────┐    ┌────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌───────────────┐
│ 1. BASELINE  │───→│ 2. TRANSIT  │───→│ 3. STEADY    │───→│ 4. REVERSIBILITY│───→│ 5. RETRO-     │
│              │    │    ION      │    │    STATE     │    │    PROBE        │    │    ANALYSIS   │
│ Scarcity     │    │ Parametric  │    │ Post-scarcity│    │ Re-inject       │    │ Trace what    │
│ economy. All │    │ scarcity    │    │ plateau.     │    │ scarcity.       │    │ replaced what.│
│ 7 mechanisms │    │ reduction.  │    │ Measure      │    │ Mechanisms that  │    │ Map functional│
│ active.      │    │ Track       │    │ sustained    │    │ recover = dormant│    │ replacement   │
│ Establish    │    │ mechanism   │    │ adoption +   │    │ persist (not     │    │ chains.       │
│ baselines.   │    │ responses.  │    │ coordination │    │ collapse).       │    │               │
│              │    │             │    │ efficiency.  │    │ Non-recovery =   │    │               │
│              │    │             │    │              │    │ confirmed dead.  │    │               │
└─────────────┘    └────────────┘    └──────────────┘    └─────────────────┘    └───────────────┘
```

### Phase 1: Baseline (Scarcity Economy)

**Duration:** Long enough for all mechanisms to reach adoption equilibrium.

**Conditions:** Material goods are scarce. Agents must coordinate to survive. All 7 mechanisms are available (not imposed — agents choose which to use).

**Measurements:**
- Baseline adoption rate for each mechanism (% of agents actively using it)
- Baseline coordination efficiency for each mechanism (entropy reduction vs. random allocation)
- Baseline behavioral pattern signatures (what does "pricing behavior" look like in this simulation's data? What does "employment behavior" look like? Needed for Phase 3 repurpose detection.)

**Exit condition:** Adoption rates have stabilized (variance < threshold for M consecutive cycles). The economy is in steady state.

### Phase 2: Transition

**Duration:** Variable — this is the key parameter. Fast (5-10 cycles), medium (50-100), slow (500+).

**Conditions:** Scarcity parameters decrease over the phase duration. Material goods become progressively cheaper / more abundant. The transition can be:
- **Uniform**: All goods become abundant simultaneously
- **Sectoral**: Some goods become abundant before others (e.g., information first, then manufactured goods, then location-bound services)
- **Patchy**: Abundance arrives unevenly across agent subpopulations (some agents experience post-scarcity while others are still in scarcity)

**Measurements:**
- Mechanism adoption rates (tracked per cycle — this produces the adoption curve)
- Coordination efficiency per mechanism (is the mechanism still solving problems or running idle?)
- Agent stress indicators (purpose/engagement scores, coordination failures, unmet needs)
- Path dependence markers: which mechanism changes first? Do early changes cascade?

**Exit condition:** Scarcity parameters have reached post-scarcity floor across all goods and all agents.

### Phase 3: Steady State (Post-Scarcity Plateau)

**Duration:** At least as long as Phase 1. Mechanisms need equivalent time to either stabilize in new roles or fully collapse.

**Conditions:** Material scarcity is effectively zero. Remaining scarce goods (attention, status, location, time) persist. No external shocks.

**Measurements:**
- Sustained adoption rates (for collapse detection: has any mechanism dropped below 5% for N consecutive cycles?)
- Coordination efficiency per surviving mechanism (for persist/idle detection)
- Behavioral pattern matching (for repurpose detection: are mechanisms exhibiting the same behavioral patterns as baseline but on different goods?)
- Information structure check on pattern matches (discovery vs. labeling — see measurement framework)
- Novel coordination patterns not matching any of the 7 baseline mechanisms

**Exit condition:** All mechanisms have either stabilized above threshold, stabilized below threshold, or are exhibiting a clear trend. No mechanism is still in rapid flux.

### Phase 4: Reversibility Probe

**Duration:** Short — enough to test recovery, not enough to re-establish a full scarcity economy. Roughly 20-30% of Phase 1 duration.

**Conditions:** Temporarily re-inject material scarcity. Not a full return to baseline — a shock, like a supply disruption. The question is whether dormant mechanisms reactivate.

**Measurements:**
- For each mechanism that dropped below threshold in Phase 3:
  - Does adoption recover when scarcity returns? → **Dormant persist** (not collapse)
  - Does adoption stay near zero? → **Confirmed collapse** (irreversible)
- Recovery speed: how quickly do dormant mechanisms reactivate? (Fast recovery = strong persist. Slow/partial recovery = weak persist.)
- For mechanisms that stayed above threshold in Phase 3: do they intensify under re-injected scarcity? (Tests whether repurposed mechanisms revert to original function or maintain their new role.)

**Exit condition:** Recovery/non-recovery is clear for all below-threshold mechanisms.

### Phase 5: Retroanalysis

**Not a simulation phase — a post-processing step.** Run after Phase 4 data is collected.

**For each confirmed collapse (non-recovery in Phase 4):**
1. Identify the cycle range where adoption dropped below threshold
2. Trace what coordination activity replaced it — which other mechanisms saw adoption increases in the same cycle range?
3. Map the functional replacement chain: "Money collapsed in cycles 80-120. In cycles 90-130, reputation-based coordination increased by X% and domain-specific token systems emerged."
4. Check whether the replacement mechanism was a repurposed existing mechanism or a novel pattern

**For each confirmed repurpose:**
1. Run the information structure check (discovery vs. labeling)
2. Quantify the behavioral similarity score between baseline and post-scarcity instances
3. Identify what new goods the mechanism is now coordinating

**Output:** The final mechanism × outcome matrix with simulation-validated verdicts replacing the prior hypotheses.

---

## Agent Model

### Design Tension

The central tradeoff: **autonomy vs. measurability**.

- **Maximum autonomy** (LLM-based agents with free-form reasoning): Can invent novel coordination mechanisms, reason about their choices, adapt creatively. But outputs are unstructured text — hard to extract adoption rates and efficiency metrics reliably.
- **Maximum measurability** (rule-based agents with coded behavioral options): Clean numerical outputs, deterministic measurement. But agents can only do what was programmed — cannot falsify hypotheses because they cannot invent alternatives.

### Architecture: Structured Autonomy

Agents are LLM-powered but operate within a structured action space that produces measurable outputs.

**Each cycle, each agent:**
1. **Observes** the environment state (available goods, scarcity levels, other agents' recent actions)
2. **Reasons** (LLM call) about what coordination strategy to use, given their persona, goals, and observations
3. **Acts** by selecting from a structured action vocabulary *or* proposing a novel action (free-form, flagged for classification)
4. **Reports** a structured output: what they did, what mechanism it used, what they were trying to coordinate

The structured action vocabulary covers the 7 known mechanisms:

| Action type | Mechanism | Structured output fields |
|-------------|-----------|--------------------------|
| `bid` / `ask` / `accept_price` | Price signals | good_type, price_offered, price_accepted |
| `pay` / `receive` / `save` / `lend` | Money | token_type, amount, counterparty, purpose |
| `claim` / `contest` / `enforce` / `transfer` | Property rights | asset_type, claim_type, enforced (bool) |
| `offer_work` / `accept_work` / `compensate` | Employment | task_type, compensation_type, duration, voluntary (bool) |
| `contribute` / `collect` / `distribute` | Taxation | pool_id, amount, distribution_target |
| `rate` / `endorse` / `check_reputation` | Reputation | target_agent, score_change, basis |
| `join_queue` / `advance` / `serve_next` | Queuing | resource_type, position, arrival_time |
| `custom` | Novel / unclassified | free_text_description (classified post-hoc) |

**The `custom` action is critical.** It allows agents to invent coordination mechanisms not anticipated by the design. Any `custom` action is logged with its free-text description and classified during retroanalysis. If a pattern of `custom` actions emerges across multiple agents, it is a candidate for a novel mechanism — exactly the kind of emergent outcome the simulation is designed to detect.

### Agent Personas

Agents are initialized with personas that shape their reasoning but do not deterministically dictate their behavior. Persona dimensions:

| Dimension | Range | Effect |
|-----------|-------|--------|
| **Work identity** | Strong ↔ Weak | How much of the agent's self-concept is tied to employment. Strong work-identity agents resist employment collapse longer. |
| **Adaptability** | High ↔ Low | How quickly the agent adjusts coordination strategies when conditions change. |
| **Social orientation** | Individual ↔ Communal | Preference for individual mechanisms (property, money) vs. collective ones (reputation, taxation). |
| **Risk tolerance** | High ↔ Low | Willingness to try novel coordination strategies vs. sticking with known ones. |
| **Resource level** | High ↔ Low | Starting material wealth. Tests whether initial inequality affects mechanism adoption during transition. |

**Population mix:** Agents are drawn from a distribution across these dimensions — not uniform, not extreme. The distribution itself is a tunable parameter (what happens if most agents have strong work identity? what if most are highly adaptable?).

### Agent Count

The simulation runs a pilot phase at 5–10 agents and production runs at 100 agents.

**Pilot (5–10 agents):** Validates the pipeline before the full sweep — confirms Mesa scheduling, LLM call loop, data collection, and verdict classification all work correctly. Not publication-quality but fast and inexpensive.

**Production (100 agents):** Full parameter sweep runs. A 5% collapse threshold corresponds to 5 agents — clean collapse/persist detection. 100 agents provides better statistical power and more realistic social dynamics.

**Each run:** Same persona distribution, different random seed → different interaction patterns → tests result robustness across stochastic variation.

---

## Environment Model

### Goods

The simulation world contains two categories of goods:

**Material goods** (scarcity-adjustable):
- Food/shelter (basic survival)
- Manufactured goods (comfort, tools)
- Information/knowledge (education, entertainment)

Each has a **scarcity parameter** (0.0 = fully abundant, 1.0 = extremely scarce) that the run protocol adjusts across phases.

**Inherently scarce goods** (always scarce regardless of phase):
- **Attention** — each agent has a fixed attention budget per cycle. Cannot be manufactured.
- **Status** — relative ranking. Zero-sum by definition.
- **Location** — desirable positions in the agent network (high connectivity, central). Fixed supply.
- **Unique experiences** — one-time interactions, creative works, unrepeatable events. Inherently rivalrous.

This two-category structure is what makes repurpose testable. If a mechanism collapses for material goods but activates for inherently scarce goods, that is repurpose. If it collapses for both, that is collapse. If it continues for material goods despite abundance, that is persist (idle).

### Scarcity Parameter Function

During Phase 2 (transition), the scarcity parameter for material goods follows a configurable curve:

- **Linear**: scarcity(t) = 1.0 - (t / T)
- **Exponential**: scarcity(t) = e^(-kt) (fast initial drop, long tail)
- **Step function**: scarcity(t) jumps from 1.0 to 0.0 at time T (sudden post-scarcity — hardest stress test)
- **Sectoral**: different goods follow different curves (information first, then manufactured, then location-bound)

### Interaction Structure

Agents interact in a network, not all-to-all. Network topology is a tunable parameter:

- **Small world**: Realistic social structure. Most interactions are local, some long-range connections.
- **Scale-free**: Some agents are hubs (high connectivity). Tests whether influential agents drive mechanism adoption.
- **Random**: Baseline. No structure.

Each cycle, each agent can interact with N neighbors (N = interaction budget, another tunable parameter).

---

## Output Specification

### Per-Mechanism, Per-Cycle Signals

Every cycle, for every mechanism, the simulation computes three numbers:

| Signal | What it measures | How it's computed |
|--------|-----------------|-------------------|
| **Adoption rate** | What fraction of agents used this mechanism this cycle | count(agents who took an action of this mechanism type) / total_agents |
| **Coordination efficiency** | Is the mechanism actually solving an allocation problem | Entropy of resource allocation with mechanism vs. entropy of random allocation. Ratio > 1 = coordinating. Ratio ≈ 1 = idle. |
| **Behavioral pattern score** | How similar is current behavior to the baseline pattern | Cosine similarity between the distribution of action subtypes (bid/ask/accept) this cycle vs. baseline distribution. High similarity + different goods = repurpose signal. |

### Verdict Classification (Post-Run)

After all phases complete, each mechanism is classified according to the following decision tree:

```
IF adoption_rate < 0.05 for N consecutive cycles in Phase 3:
    IF mechanism recovers in Phase 4 (reversibility probe):
        verdict = PERSIST (dormant)
    ELSE:
        verdict = COLLAPSE (irreversible)
ELIF adoption_rate >= 0.05 AND coordination_efficiency ≈ 1.0:
    verdict = PERSIST (idle)
ELIF adoption_rate >= 0.05 AND coordination_efficiency > 1.0:
    IF behavioral_pattern_score > threshold AND goods_domain ≠ baseline:
        run information_structure_check:
            IF discovery_process: verdict = REPURPOSE (confirmed)
            IF labeling_process: verdict = NOVEL_MECHANISM (flagged)
    ELIF behavioral_pattern_score > threshold AND goods_domain = baseline:
        verdict = PERSIST (active — still solving original problem)
    ELIF behavioral_pattern_score < threshold:
        verdict = NOVEL_MECHANISM (new pattern)
```

Note: the classification tree includes `NOVEL_MECHANISM` as a fourth outcome. The three-outcome framework (collapse/persist/repurpose) may be insufficient — the simulation is capable of revealing that.

---

## Technical Stack

### Framework Selection

The simulation is built on **Mesa 3 with direct LLM API calls**.

Mesa 3 (published JOSS March 2025) handles the simulation loop, agent scheduling, small-world network topology (via NetworkX), BatchRunnerMP for parallel parameter sweeps, and data collection to pandas DataFrames.

Agent reasoning: each agent's reasoning step makes a direct LLM API call. The agent receives its persona, environment state, and available action vocabulary as a structured prompt and returns a structured action from the vocabulary table above. LLM calls are routed through an `AgentReasoner` class — not through Mesa-LLM.

**Why not Mesa-LLM (v0.2.0, Feb 2026):** A dedicated Mesa + LLM integration package exists and supports Anthropic, OpenAI, xAI, and others. However, it carries an "API may change significantly" status with no stable 1.0 release. For a peer-reviewed study where reproducibility is a first-class concern, depending on an unstable library introduces long-term fragility. Direct API calls are used instead; Mesa-LLM can be evaluated at 1.0.

**Why not LangGraph/CrewAI:** These frameworks are optimized for task pipelines, not parametric sweeps. They lack Mesa's native agent scheduling, network topology generators, and BatchRunnerMP. Building a custom simulation layer on top would negate any integration benefit.

**Why not custom lightweight Python:** Mesa's BatchRunnerMP, NetworkX topology generators, and DataCollector provide substantial scaffolding value. A custom implementation would require rebuilding these at greater upfront cost.

---

## Simulation Parameters

### Formal Parameter Table

| Parameter | Type | Description | Phase 1 value / sweep range |
|-----------|------|-------------|------------------------------|
| `transition_rate` | `int` | Phase 2 duration in cycles — primary experimental variable | Sweep: `[5, 25, 100, 500]` |
| `scarcity_curve` | `str` | Shape of scarcity decay during Phase 2 | Sweep: `["linear", "exponential", "step"]` |
| `random_seed` | `int` | Stochastic variation seed | Min 3 seeds per combination |
| `n_agents` | `int` | Population size | 100 (production); 5–10 (pilot) |
| `phase1_cycles` | `int` | Baseline phase duration | Fixed: 200 |
| `phase3_cycles` | `int` | Steady-state phase duration | Fixed: 200 |
| `phase4_cycles` | `int` | Reversibility probe duration | Fixed: 50 |
| `network_topology` | `str` | Agent interaction network structure | Fixed: `"small_world"` |
| `interaction_budget` | `int` | Max neighbors per agent per cycle | Fixed: 3 |
| `collapse_threshold` | `float` | Adoption below which mechanism is candidate collapse | Fixed: 0.05 |
| `collapse_sustained_n` | `int` | Consecutive cycles below threshold to trigger probe | Fixed: 20 |

### Transition Rate Encoding

`transition_rate` is the primary experimental variable. It encodes transition speed as the number of cycles Phase 2 lasts before material scarcity reaches floor (0.0).

```python
transition_rate: int  # choices: 5, 25, 100, 500

# Interpretation:
# 5   → "shock"    — sudden post-scarcity arrival; hardest mechanism stress test
# 25  → "rapid"    — fast transition (~decade-scale analogue)
# 100 → "moderate" — generation-scale transition
# 500 → "gradual"  — mechanisms have time to adapt before scarcity ends
```

**Scarcity decay functions** (applied to all material goods during Phase 2):

```python
def scarcity_at(t: int, transition_rate: int, curve: str) -> float:
    """Material goods scarcity level at cycle t of Phase 2. Returns 0.0–1.0."""
    progress = t / transition_rate  # 0.0 → 1.0
    if curve == "linear":
        return max(0.0, 1.0 - progress)
    elif curve == "exponential":
        return math.exp(-5 * progress)   # fast initial drop, long tail
    elif curve == "step":
        return 0.0 if progress >= 1.0 else 1.0   # binary flip at endpoint
```

### Minimum Parameter Sweep

`4 transition_rates × 3 scarcity_curves × 3 seeds = 36 runs`

### LLM Configuration

- **Primary model**: xAI `grok-4.x-fast-reasoning` (latest available at build time). The reasoning variant is preferred: agents reason through coordination strategy before acting, producing higher-quality structured action selection. The model name is abstracted behind an `AgentReasoner` class as a single config value.
- **Retroanalysis model**: `grok-4-0709` or equivalent — used for novel action classification and information structure checks (low volume, higher reasoning quality).
- **Batch API** is used for all per-cycle calls. LLM call volume scales linearly with agent count × total cycles per run.

---

## Output Data Schema

Two required CSVs per run, plus one optional novel-action log.

### `cycle_data.csv` — Time-series measurements

One row per `(run_id, cycle, mechanism)`:

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | int | Unique run identifier |
| `seed` | int | Random seed |
| `transition_rate` | int | Phase 2 duration parameter |
| `scarcity_curve` | str | Decay function shape |
| `n_agents` | int | Population size |
| `cycle` | int | Simulation cycle (0-indexed) |
| `phase` | str | `baseline` / `transition` / `steady_state` / `reversibility` |
| `material_scarcity` | float | Current scarcity level for material goods (0.0–1.0) |
| `mechanism` | str | `price` / `money` / `property` / `employment` / `taxation` / `reputation` / `queuing` |
| `adoption_rate` | float | Fraction of agents using this mechanism this cycle (0.0–1.0) |
| `coordination_efficiency` | float | Entropy ratio vs. random allocation (>1.0 = coordinating, ≈1.0 = idle) |
| `behavioral_pattern_score` | float | Cosine similarity to Phase 1 baseline action distribution (0.0–1.0) |
| `custom_action_count` | int | Novel/unclassified (`custom`) actions this cycle |

### `run_summary.csv` — Post-run verdict classification

One row per `(run_id, mechanism)`:

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | int | Unique run identifier |
| `seed` | int | Random seed |
| `transition_rate` | int | Phase 2 duration |
| `scarcity_curve` | str | Decay function shape |
| `n_agents` | int | Population size |
| `mechanism` | str | Mechanism name |
| `verdict` | str | `COLLAPSE` / `PERSIST_DORMANT` / `PERSIST_IDLE` / `PERSIST_ACTIVE` / `REPURPOSE` / `NOVEL_MECHANISM` |
| `phase3_mean_adoption` | float | Mean adoption rate across all Phase 3 cycles |
| `phase3_min_adoption` | float | Minimum adoption rate in Phase 3 (collapse detection signal) |
| `phase4_recovery` | bool | Did mechanism recover above threshold when scarcity was re-injected? |
| `repurpose_goods_domain` | str | For REPURPOSE: which goods domain is mechanism now coordinating (null otherwise) |
| `information_structure` | str | `DISCOVERY` / `LABELING` / `NA` — result of information structure check |
| `hypothesis_confirmed` | bool | Does verdict match the prior hypothesis? |

### `novel_actions.csv` — Novel mechanism log (optional)

One row per `custom` action taken by an agent. Used during retroanalysis to identify emergent coordination patterns.

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | int | Run identifier |
| `cycle` | int | Cycle of the action |
| `agent_id` | int | Agent identifier |
| `persona_work_identity` | float | Agent's work identity score (0.0–1.0) |
| `persona_adaptability` | float | Agent's adaptability score (0.0–1.0) |
| `free_text_description` | str | Agent's LLM-generated description of the novel action |
| `classified_as` | str | Post-hoc classification populated during retroanalysis (null until classified) |

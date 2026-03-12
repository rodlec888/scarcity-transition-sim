"""
@file environment.py
@description Mesa Model: goods, scarcity parameters, small-world network, phase controller.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-04
@changelog
- 2026-03-04: v1.0.0 - Initial creation
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import mesa
import networkx as nx

from src.config import MECHANISMS, SimConfig

if TYPE_CHECKING:
    from src.agent import CoordinationAgent


# Material goods (scarcity-adjustable)
MATERIAL_GOODS = ("food_shelter", "manufactured", "information")

# Inherently scarce goods (always scarce regardless of phase)
INHERENT_GOODS = ("attention", "status", "location", "unique_experiences")


class ScarcityModel(mesa.Model):
    """ABM of economic coordination mechanisms under parametric scarcity transition.

    Args:
        config: Simulation configuration. All parameters come from here.
    """

    def __init__(self, config: SimConfig | None = None):
        super().__init__(seed=config.random_seed if config else 42)
        self.config = config or SimConfig()
        self.cycle: int = 0

        # Build small-world network
        k = min(self.config.interaction_budget * 2, self.config.n_agents - 1)
        k = max(k, 2)  # watts-strogatz requires k >= 2
        self.network = nx.watts_strogatz_graph(
            n=self.config.n_agents,
            k=k,
            p=0.1,  # rewiring probability
            seed=self.config.random_seed,
        )

        # Current scarcity levels per good
        self.material_scarcity: float = self.config.material_scarcity_at(0)
        self.goods: dict[str, float] = {}
        self._update_goods()

        # Per-cycle mechanism usage tracking (reset each step)
        self.cycle_actions: list[dict] = []

        # Baseline behavioral patterns (captured at end of Phase 1)
        self.baseline_patterns: dict[str, dict] | None = None

        # Create agents (imported late to avoid circular import)
        from src.agent import CoordinationAgent

        for node_id in self.network.nodes:
            CoordinationAgent.create(self, node_id)

    @property
    def phase(self) -> str:
        return self.config.phase_at(self.cycle)

    @property
    def agents_list(self) -> list[CoordinationAgent]:
        """Typed accessor for all agents."""
        return list(self.agents)

    def neighbors_of(self, node_id: int) -> list[int]:
        """Return neighbor node IDs for an agent's network position."""
        return list(self.network.neighbors(node_id))

    def step(self):
        """Advance the simulation by one cycle (synchronous)."""
        # Update scarcity
        self.material_scarcity = self.config.material_scarcity_at(self.cycle)
        self._update_goods()

        # Reset per-cycle tracking
        self.cycle_actions = []

        # All agents act
        self.agents.shuffle_do("step")

        # Capture baseline at end of Phase 1
        if (
            self.baseline_patterns is None
            and self.cycle == self.config.phase1_cycles - 1
        ):
            self.baseline_patterns = self._compute_behavioral_patterns()

        self.cycle += 1

    async def async_step(self):
        """Advance the simulation by one cycle with concurrent agent reasoning.

        All agents observe synchronously (snapshot of current state), then all
        LLM calls fire concurrently via asyncio.gather. Actions are recorded
        sequentially after all responses arrive — preserving deterministic
        cycle boundaries while parallelizing the API-bound work.
        """
        # Update scarcity
        self.material_scarcity = self.config.material_scarcity_at(self.cycle)
        self._update_goods()

        # Reset per-cycle tracking
        self.cycle_actions = []

        # Shuffle agent order (reproducible via seeded RNG)
        agents = self.agents_list
        self.random.shuffle(agents)

        # All agents observe synchronously (snapshot of current state)
        agent_obs = [(agent, agent.observe()) for agent in agents]

        # Fire all LLM calls concurrently
        from src.reasoner import AgentReasoner

        reasoner = AgentReasoner.get_instance()
        tasks = [
            reasoner.async_decide(agent, obs) for agent, obs in agent_obs
        ]
        results = await asyncio.gather(*tasks)

        # Apply actions sequentially (deterministic recording order)
        for (agent, _obs), action in zip(agent_obs, results):
            if action:
                agent._execute_action(action)

        # Capture baseline at end of Phase 1
        if (
            self.baseline_patterns is None
            and self.cycle == self.config.phase1_cycles - 1
        ):
            self.baseline_patterns = self._compute_behavioral_patterns()

        self.cycle += 1

    def _update_goods(self):
        """Update scarcity levels for all goods."""
        for good in MATERIAL_GOODS:
            self.goods[good] = self.material_scarcity
        for good in INHERENT_GOODS:
            self.goods[good] = 1.0  # always scarce

    def _compute_behavioral_patterns(self) -> dict[str, dict]:
        """Compute action subtype distribution per mechanism from current cycle actions.

        Returns:
            Dict mapping mechanism name to a dict of {action_subtype: count}.
        """
        patterns: dict[str, dict[str, int]] = {m: {} for m in MECHANISMS}
        for action in self.cycle_actions:
            mech = action.get("mechanism")
            subtype = action.get("action_type")
            if mech in patterns and subtype:
                patterns[mech][subtype] = patterns[mech].get(subtype, 0) + 1
        return patterns

    def record_action(self, action: dict):
        """Record a structured action taken by an agent this cycle."""
        self.cycle_actions.append(action)

    def compute_adoption_rates(self) -> dict[str, float]:
        """Fraction of agents that used each mechanism this cycle."""
        if not self.config.n_agents:
            return {m: 0.0 for m in MECHANISMS}

        users: dict[str, set] = {m: set() for m in MECHANISMS}
        for action in self.cycle_actions:
            mech = action.get("mechanism")
            agent_id = action.get("agent_id")
            if mech in users and agent_id is not None:
                users[mech].add(agent_id)

        return {m: len(users[m]) / self.config.n_agents for m in MECHANISMS}

    def compute_custom_action_count(self) -> int:
        """Count of custom (novel) actions this cycle."""
        return sum(1 for a in self.cycle_actions if a.get("mechanism") == "custom")

"""
@file agent.py
@description Mesa Agent: persona initialization, structured action vocabulary, step() loop.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-04
@changelog
- 2026-03-04: v1.0.0 - Initial creation
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import mesa

if TYPE_CHECKING:
    from src.environment import ScarcityModel


# Structured action vocabulary — maps mechanism to valid action subtypes
ACTION_VOCABULARY: dict[str, list[str]] = {
    "price": ["bid", "ask", "accept_price"],
    "money": ["pay", "receive", "save", "lend"],
    "property": ["claim", "contest", "enforce", "transfer"],
    "employment": ["offer_work", "accept_work", "compensate"],
    "taxation": ["contribute", "collect", "distribute"],
    "reputation": ["rate", "endorse", "check_reputation"],
    "queuing": ["join_queue", "advance", "serve_next"],
    "custom": ["custom"],
}

# All valid action types (flat set for validation)
ALL_ACTION_TYPES = {at for subtypes in ACTION_VOCABULARY.values() for at in subtypes}


class Persona:
    """Agent personality dimensions that shape reasoning without dictating behavior.

    All dimensions are floats in [0.0, 1.0].
    """

    __slots__ = (
        "work_identity",
        "adaptability",
        "social_orientation",
        "risk_tolerance",
        "resource_level",
    )

    def __init__(
        self,
        work_identity: float,
        adaptability: float,
        social_orientation: float,
        risk_tolerance: float,
        resource_level: float,
    ):
        self.work_identity = work_identity
        self.adaptability = adaptability
        self.social_orientation = social_orientation
        self.risk_tolerance = risk_tolerance
        self.resource_level = resource_level

    def to_dict(self) -> dict[str, float]:
        return {s: getattr(self, s) for s in self.__slots__}

    def describe(self) -> str:
        """Human-readable persona summary for LLM prompt context."""
        labels = {
            "work_identity": ("weak work identity", "strong work identity"),
            "adaptability": ("slow to adapt", "highly adaptable"),
            "social_orientation": ("individualist", "communal"),
            "risk_tolerance": ("risk-averse", "risk-seeking"),
            "resource_level": ("low resources", "high resources"),
        }
        parts = []
        for dim, (low, high) in labels.items():
            val = getattr(self, dim)
            label = high if val > 0.5 else low
            parts.append(f"{label} ({val:.2f})")
        return ", ".join(parts)


class CoordinationAgent(mesa.Agent):
    """An agent that reasons about coordination strategies using an LLM.

    Args:
        model: The ScarcityModel instance.
        node_id: Position in the interaction network.
    """

    def __init__(self, model: ScarcityModel, node_id: int):
        super().__init__(model)
        self.node_id = node_id
        self.persona: Persona | None = None
        self.action_history: list[dict[str, Any]] = []

    @classmethod
    def create(cls, model: ScarcityModel, node_id: int) -> CoordinationAgent:
        """Factory that creates an agent with a seeded random persona."""
        agent = cls(model, node_id)
        rng = model.random

        agent.persona = Persona(
            work_identity=rng.random(),
            adaptability=rng.random(),
            social_orientation=rng.random(),
            risk_tolerance=rng.random(),
            resource_level=rng.random(),
        )
        return agent

    @property
    def scarcity_model(self) -> ScarcityModel:
        return self.model  # type: ignore[return-value]

    def observe(self) -> dict[str, Any]:
        """Gather observations about the environment and neighbors."""
        model = self.scarcity_model
        neighbor_ids = model.neighbors_of(self.node_id)

        # Recent actions by neighbors (this cycle so far)
        neighbor_actions = [
            a for a in model.cycle_actions if a.get("agent_id") in neighbor_ids
        ]

        # Collect neighbor action histories for behavioral summary
        neighbor_histories: list[list[dict[str, Any]]] = []
        for agent in model.agents_list:
            if agent.node_id in neighbor_ids:
                neighbor_histories.append(agent.action_history)

        return {
            "cycle": model.cycle,
            "phase": model.phase,
            "material_scarcity": model.material_scarcity,
            "goods": dict(model.goods),
            "neighbor_ids": neighbor_ids,
            "neighbor_recent_actions": neighbor_actions[-10:],  # cap for prompt size
            "neighbor_histories": neighbor_histories,
            "own_recent_actions": self.action_history[-5:],
        }

    def step(self):
        """One simulation cycle: observe -> reason -> act -> record (synchronous)."""
        from src.reasoner import AgentReasoner

        observations = self.observe()
        reasoner = AgentReasoner.get_instance()
        action = reasoner.decide(self, observations)

        if action:
            self._execute_action(action)

    async def async_step(self):
        """One simulation cycle: observe -> reason -> act -> record (async).

        Observations are gathered synchronously (local state only), then the
        LLM call fires asynchronously. Execution and recording are synchronous.
        """
        from src.reasoner import AgentReasoner

        observations = self.observe()
        reasoner = AgentReasoner.get_instance()
        action = await reasoner.async_decide(self, observations)

        if action:
            self._execute_action(action)

    def _execute_action(self, action: dict[str, Any]):
        """Validate, record, and report a structured action."""
        # Ensure agent_id is present
        action["agent_id"] = self.unique_id
        action["node_id"] = self.node_id
        action["cycle"] = self.scarcity_model.cycle

        # Validate mechanism and action_type
        mechanism = action.get("mechanism", "custom")
        action_type = action.get("action_type", "custom")

        if mechanism not in ACTION_VOCABULARY:
            mechanism = "custom"
            action["mechanism"] = "custom"

        if action_type not in ALL_ACTION_TYPES:
            action_type = "custom"
            action["action_type"] = "custom"

        # Record locally and on the model
        self.action_history.append(action)
        self.scarcity_model.record_action(action)

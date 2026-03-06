"""
@file conftest.py
@description Shared pytest fixtures for scarcity-transition-sim test suite.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-05
@changelog
- 2026-03-05: v1.0.0 - Initial creation
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import pytest

from src.agent import ACTION_VOCABULARY, CoordinationAgent
from src.config import SimConfig
from src.environment import ScarcityModel


# ---------------------------------------------------------------------------
# Mock reasoner
# ---------------------------------------------------------------------------

_STANDARD_MECHANISMS = [m for m in ACTION_VOCABULARY if m != "custom"]


class MockReasoner:
    """Drop-in replacement for AgentReasoner that returns deterministic actions.

    Cycles through the 7 standard mechanisms round-robin based on the cycle
    number in observations. Makes ZERO API calls.
    """

    _call_count: int = 0

    def decide(self, agent: CoordinationAgent, observations: dict[str, Any]) -> dict[str, Any]:
        cycle = observations.get("cycle", 0)
        mech = _STANDARD_MECHANISMS[cycle % len(_STANDARD_MECHANISMS)]
        action_type = ACTION_VOCABULARY[mech][0]
        self._call_count += 1
        return {
            "mechanism": mech,
            "action_type": action_type,
            "target_good": "food_shelter",
            "counterparty": None,
            "reasoning": f"Mock action for cycle {cycle}",
            "details": {},
        }

    @property
    def call_count(self) -> int:
        return self._call_count

    @classmethod
    def get_instance(cls) -> MockReasoner:
        """Mimic singleton API so agent.step() works transparently."""
        # The monkeypatch in the fixture handles routing; this is a fallback.
        raise RuntimeError("MockReasoner.get_instance should not be called directly")

    @classmethod
    def reset(cls) -> None:
        pass


@pytest.fixture()
def mock_reasoner(monkeypatch):
    """Patch the AgentReasoner singleton so all agent.step() calls use MockReasoner.

    Guarantees ZERO real API calls. Returns the MockReasoner instance for assertions.
    """
    import src.reasoner as reasoner_mod

    fake = MockReasoner()

    # Patch the module-level singleton so get_instance() returns our fake
    monkeypatch.setattr(reasoner_mod, "_reasoner_instance", fake)

    # Also patch get_instance on the class to always return the fake,
    # in case anyone calls AgentReasoner.get_instance() directly.
    monkeypatch.setattr(reasoner_mod.AgentReasoner, "get_instance", classmethod(lambda cls: fake))

    return fake


# ---------------------------------------------------------------------------
# Config and model fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def seeded_config() -> SimConfig:
    """Small, fast SimConfig for unit tests."""
    return SimConfig(
        transition_rate=5,
        scarcity_curve="linear",
        random_seed=42,
        n_agents=5,
        phase1_cycles=5,
        phase3_cycles=5,
        phase4_cycles=3,
    )


@pytest.fixture()
def seeded_model(seeded_config, mock_reasoner) -> ScarcityModel:
    """A ScarcityModel wired with mock_reasoner, ready to step."""
    from src.collector import create_collector

    model = ScarcityModel(seeded_config)
    model.datacollector = create_collector()
    return model


@pytest.fixture()
def tmp_output_dir(tmp_path) -> Path:
    """Temporary directory for CSV output tests."""
    d = tmp_path / "outputs"
    d.mkdir()
    return d

"""
@file conftest.py
@description Shared pytest fixtures for scarcity-transition-sim test suite.
@author ScarcityTransitionSim_Dev
@version 1.1.0
@date 2026-03-05
@changelog
- 2026-03-05: v1.0.0 - Initial creation
- 2026-11-22: v1.1.0 - Every test gets placeholder xAI settings, whatever .env holds
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import pytest

from src.agent import ACTION_VOCABULARY, CoordinationAgent
from src.config import SimConfig
from src.environment import ScarcityModel


# ---------------------------------------------------------------------------
# Environment isolation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_xai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give every test the same xAI settings, whatever the machine's `.env` holds.

    `src.reasoner` loads `.env` when it is imported. Without this fixture the
    suite passes only where a developer's `.env` sets `XAI_MODEL`, and a test
    that sets no key of its own runs with the real `XAI_API_KEY`. Placeholders
    make the suite behave the same locally and in CI. A test that needs a
    variable changed or absent sets or deletes it itself, after this runs.
    """
    monkeypatch.setenv("XAI_MODEL", "test-model-not-real")
    monkeypatch.setenv("XAI_API_KEY", "test-key-not-real")
    monkeypatch.delenv("XAI_API_BASE_URL", raising=False)
    monkeypatch.delenv("XAI_MAX_CONCURRENT", raising=False)


# ---------------------------------------------------------------------------
# Mock reasoner
# ---------------------------------------------------------------------------

_STANDARD_MECHANISMS = [m for m in ACTION_VOCABULARY if m != "custom"]


class MockReasoner:
    """Drop-in replacement for AgentReasoner that returns deterministic actions.

    Cycles through the 7 standard mechanisms round-robin based on the cycle
    number in observations. Makes ZERO API calls. Supports both sync and async.
    """

    _call_count: int = 0

    def _make_action(self, observations: dict[str, Any]) -> dict[str, Any]:
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

    def decide(self, agent: CoordinationAgent, observations: dict[str, Any]) -> dict[str, Any]:
        return self._make_action(observations)

    async def async_decide(self, agent: CoordinationAgent, observations: dict[str, Any]) -> dict[str, Any]:
        return self._make_action(observations)

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

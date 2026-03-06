"""
@file test_agent.py
@description Tests for CoordinationAgent, Persona, and ACTION_VOCABULARY.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-05
@changelog
- 2026-03-05: v1.0.0 - Initial creation
"""

from __future__ import annotations

import pytest

from src.agent import ACTION_VOCABULARY, ALL_ACTION_TYPES, CoordinationAgent, Persona
from src.config import MECHANISMS, SimConfig
from src.environment import ScarcityModel


# ---------------------------------------------------------------------------
# Persona
# ---------------------------------------------------------------------------

class TestPersona:

    def test_to_dict_keys(self):
        p = Persona(0.1, 0.2, 0.3, 0.4, 0.5)
        d = p.to_dict()
        assert set(d.keys()) == {
            "work_identity", "adaptability", "social_orientation",
            "risk_tolerance", "resource_level",
        }

    def test_to_dict_values(self):
        p = Persona(0.1, 0.2, 0.3, 0.4, 0.5)
        d = p.to_dict()
        assert d["work_identity"] == pytest.approx(0.1)
        assert d["resource_level"] == pytest.approx(0.5)

    def test_describe_returns_string(self):
        p = Persona(0.1, 0.9, 0.3, 0.7, 0.5)
        desc = p.describe()
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_describe_contains_all_dimensions(self):
        p = Persona(0.1, 0.9, 0.3, 0.7, 0.5)
        desc = p.describe()
        # Each dimension should contribute a label
        assert "0.10" in desc  # work_identity
        assert "0.90" in desc  # adaptability
        assert "0.30" in desc  # social_orientation
        assert "0.70" in desc  # risk_tolerance
        assert "0.50" in desc  # resource_level

    def test_describe_low_labels(self):
        p = Persona(0.1, 0.1, 0.1, 0.1, 0.1)
        desc = p.describe()
        assert "weak work identity" in desc
        assert "slow to adapt" in desc
        assert "individualist" in desc
        assert "risk-averse" in desc
        assert "low resources" in desc

    def test_describe_high_labels(self):
        p = Persona(0.9, 0.9, 0.9, 0.9, 0.9)
        desc = p.describe()
        assert "strong work identity" in desc
        assert "highly adaptable" in desc
        assert "communal" in desc
        assert "risk-seeking" in desc
        assert "high resources" in desc


# ---------------------------------------------------------------------------
# Persona determinism
# ---------------------------------------------------------------------------

class TestPersonaDeterminism:

    def test_same_seed_same_persona(self, mock_reasoner):
        """Two models with the same seed produce identical personas."""
        config = SimConfig(n_agents=3, random_seed=99, phase1_cycles=2, phase3_cycles=2, phase4_cycles=1)
        m1 = ScarcityModel(config)
        m2 = ScarcityModel(config)

        for a1, a2 in zip(m1.agents_list, m2.agents_list):
            assert a1.persona.to_dict() == a2.persona.to_dict()

    def test_different_seed_different_persona(self, mock_reasoner):
        config_a = SimConfig(n_agents=3, random_seed=1, phase1_cycles=2, phase3_cycles=2, phase4_cycles=1)
        config_b = SimConfig(n_agents=3, random_seed=2, phase1_cycles=2, phase3_cycles=2, phase4_cycles=1)
        m1 = ScarcityModel(config_a)
        m2 = ScarcityModel(config_b)

        # At least one persona dimension should differ
        dicts_a = [a.persona.to_dict() for a in m1.agents_list]
        dicts_b = [a.persona.to_dict() for a in m2.agents_list]
        assert dicts_a != dicts_b


# ---------------------------------------------------------------------------
# ACTION_VOCABULARY and ALL_ACTION_TYPES
# ---------------------------------------------------------------------------

class TestActionVocabulary:

    def test_has_all_7_mechanisms_plus_custom(self):
        expected = set(MECHANISMS) | {"custom"}
        assert set(ACTION_VOCABULARY.keys()) == expected

    def test_each_mechanism_has_subtypes(self):
        for mech, subtypes in ACTION_VOCABULARY.items():
            assert isinstance(subtypes, list)
            assert len(subtypes) >= 1, f"{mech} has no subtypes"

    def test_all_action_types_is_flat_set(self):
        assert isinstance(ALL_ACTION_TYPES, set)
        # Should include at least: bid, ask, pay, custom, ...
        assert "bid" in ALL_ACTION_TYPES
        assert "custom" in ALL_ACTION_TYPES

    def test_all_action_types_covers_vocabulary(self):
        for subtypes in ACTION_VOCABULARY.values():
            for st in subtypes:
                assert st in ALL_ACTION_TYPES


# ---------------------------------------------------------------------------
# CoordinationAgent
# ---------------------------------------------------------------------------

class TestCoordinationAgent:

    def test_create_factory(self, mock_reasoner):
        config = SimConfig(n_agents=3, random_seed=42, phase1_cycles=2, phase3_cycles=2, phase4_cycles=1)
        model = ScarcityModel(config)
        agents = model.agents_list
        assert len(agents) == 3
        for a in agents:
            assert isinstance(a, CoordinationAgent)
            assert a.persona is not None

    def test_agent_has_node_id(self, mock_reasoner):
        config = SimConfig(n_agents=3, random_seed=42, phase1_cycles=2, phase3_cycles=2, phase4_cycles=1)
        model = ScarcityModel(config)
        node_ids = {a.node_id for a in model.agents_list}
        assert node_ids == {0, 1, 2}

    def test_action_history_starts_empty(self, mock_reasoner):
        config = SimConfig(n_agents=3, random_seed=42, phase1_cycles=2, phase3_cycles=2, phase4_cycles=1)
        model = ScarcityModel(config)
        for a in model.agents_list:
            assert a.action_history == []

    def test_step_records_action(self, seeded_model):
        """After one model step, agents should have recorded actions."""
        seeded_model.step()
        # At least one agent should have a non-empty action history
        histories = [a.action_history for a in seeded_model.agents_list]
        assert any(len(h) > 0 for h in histories)

    def test_action_history_contains_required_fields(self, seeded_model):
        seeded_model.step()
        for agent in seeded_model.agents_list:
            for action in agent.action_history:
                assert "mechanism" in action
                assert "action_type" in action
                assert "agent_id" in action
                assert "node_id" in action
                assert "cycle" in action


# ---------------------------------------------------------------------------
# _execute_action validation
# ---------------------------------------------------------------------------

class TestExecuteAction:

    def test_invalid_mechanism_falls_back_to_custom(self, seeded_model):
        agent = seeded_model.agents_list[0]
        action = {
            "mechanism": "barter",
            "action_type": "trade",
            "target_good": "food_shelter",
            "counterparty": None,
            "reasoning": "test",
            "details": {},
        }
        agent._execute_action(action)
        assert action["mechanism"] == "custom"

    def test_invalid_action_type_falls_back_to_custom(self, seeded_model):
        agent = seeded_model.agents_list[0]
        action = {
            "mechanism": "price",
            "action_type": "unknown_subtype",
            "target_good": "food_shelter",
            "counterparty": None,
            "reasoning": "test",
            "details": {},
        }
        agent._execute_action(action)
        # The mechanism stays if it is valid, but the action_type flips to custom
        assert action["action_type"] == "custom"

    def test_valid_action_passes_through(self, seeded_model):
        agent = seeded_model.agents_list[0]
        action = {
            "mechanism": "price",
            "action_type": "bid",
            "target_good": "food_shelter",
            "counterparty": None,
            "reasoning": "test",
            "details": {},
        }
        agent._execute_action(action)
        assert action["mechanism"] == "price"
        assert action["action_type"] == "bid"

    def test_execute_adds_metadata(self, seeded_model):
        agent = seeded_model.agents_list[0]
        action = {
            "mechanism": "money",
            "action_type": "pay",
            "target_good": "food_shelter",
            "counterparty": None,
            "reasoning": "test",
            "details": {},
        }
        agent._execute_action(action)
        assert action["agent_id"] == agent.unique_id
        assert action["node_id"] == agent.node_id
        assert "cycle" in action

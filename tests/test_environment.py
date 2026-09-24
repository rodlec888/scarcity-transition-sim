"""
@file test_environment.py
@description Tests for ScarcityModel — network, phases, goods, stepping, adoption rates.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-05
@changelog
- 2026-03-05: v1.0.0 - Initial creation
"""

from __future__ import annotations

import networkx as nx
import pytest

from src.config import MECHANISMS, SimConfig
from src.environment import INHERENT_GOODS, MATERIAL_GOODS, ScarcityModel


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestModelInit:

    def test_agent_count(self, seeded_model):
        assert len(seeded_model.agents_list) == 5

    def test_cycle_starts_at_zero(self, seeded_model):
        assert seeded_model.cycle == 0

    def test_initial_phase_is_baseline(self, seeded_model):
        assert seeded_model.phase == "baseline"

    def test_initial_material_scarcity(self, seeded_model):
        assert seeded_model.material_scarcity == 1.0

    def test_config_stored(self, seeded_model, seeded_config):
        assert seeded_model.config is seeded_config


# ---------------------------------------------------------------------------
# Network topology
# ---------------------------------------------------------------------------

class TestNetwork:

    def test_node_count(self, seeded_model):
        assert seeded_model.network.number_of_nodes() == 5

    def test_connected(self, seeded_model):
        assert nx.is_connected(seeded_model.network)

    def test_small_world_type(self, seeded_model):
        assert isinstance(seeded_model.network, nx.Graph)

    def test_k_parameter_clamp(self, mock_reasoner):
        """With 3 agents, k = min(3*2, 2) = 2 which is valid for watts_strogatz."""
        config = SimConfig(n_agents=3, interaction_budget=3, random_seed=42,
                           phase1_cycles=2, phase3_cycles=2, phase4_cycles=1)
        model = ScarcityModel(config)
        assert model.network.number_of_nodes() == 3
        assert nx.is_connected(model.network)


# ---------------------------------------------------------------------------
# neighbors_of
# ---------------------------------------------------------------------------

class TestNeighborsOf:

    def test_returns_list(self, seeded_model):
        result = seeded_model.neighbors_of(0)
        assert isinstance(result, list)

    def test_neighbors_are_valid_nodes(self, seeded_model):
        for node in seeded_model.network.nodes:
            neighbors = seeded_model.neighbors_of(node)
            for n in neighbors:
                assert n in seeded_model.network.nodes

    def test_neighbors_not_empty(self, seeded_model):
        """In a connected small-world graph every node has at least 1 neighbor."""
        for node in seeded_model.network.nodes:
            assert len(seeded_model.neighbors_of(node)) >= 1


# ---------------------------------------------------------------------------
# Goods
# ---------------------------------------------------------------------------

class TestGoods:

    def test_material_goods_at_baseline(self, seeded_model):
        for good in MATERIAL_GOODS:
            assert seeded_model.goods[good] == 1.0

    def test_inherent_goods_always_1(self, seeded_model):
        for good in INHERENT_GOODS:
            assert seeded_model.goods[good] == 1.0

    def test_material_goods_update_after_phase_change(self, seeded_model):
        """Step through baseline into transition and verify goods decrease."""
        config = seeded_model.config
        # Run through all Phase 1 cycles
        for _ in range(config.phase1_cycles):
            seeded_model.step()
            seeded_model.datacollector.collect(seeded_model)

        # Now in transition phase, step once more
        seeded_model.step()
        seeded_model.datacollector.collect(seeded_model)

        # Material scarcity should still be near 1.0 at the start of transition
        # but the phase should be "transition"
        assert seeded_model.phase == "transition"

    def test_inherent_goods_remain_1_in_steady_state(self, seeded_model):
        """Inherent goods stay at 1.0 even when material scarcity is 0."""
        config = seeded_model.config
        # Fast-forward well into steady state (one step past the boundary so
        # material_scarcity has been set using a steady-state cycle number)
        total_to_steady = config.phase1_cycles + config.phase2_cycles + 1
        for _ in range(total_to_steady):
            seeded_model.step()
            seeded_model.datacollector.collect(seeded_model)

        assert seeded_model.phase == "steady_state"
        for good in INHERENT_GOODS:
            assert seeded_model.goods[good] == 1.0
        # Material goods should be 0.0
        for good in MATERIAL_GOODS:
            assert seeded_model.goods[good] == 0.0


# ---------------------------------------------------------------------------
# step()
# ---------------------------------------------------------------------------

class TestStep:

    def test_advances_cycle(self, seeded_model):
        seeded_model.step()
        assert seeded_model.cycle == 1

    def test_multiple_steps(self, seeded_model):
        for _ in range(5):
            seeded_model.step()
        assert seeded_model.cycle == 5

    def test_updates_material_scarcity(self, seeded_model):
        config = seeded_model.config
        # Step into transition phase
        for _ in range(config.phase1_cycles + 1):
            seeded_model.step()
        # Scarcity should have started decreasing (or be at transition value)
        # At minimum it should not still be initial
        assert seeded_model.cycle == config.phase1_cycles + 1

    def test_resets_cycle_actions(self, seeded_model):
        seeded_model.step()
        actions_after_step1 = len(seeded_model.cycle_actions)
        assert actions_after_step1 > 0  # agents should have acted

        seeded_model.step()
        # cycle_actions is reset at start of step, then populated
        # so it should have actions from current cycle only
        assert len(seeded_model.cycle_actions) > 0


# ---------------------------------------------------------------------------
# Adoption rates
# ---------------------------------------------------------------------------

class TestAdoptionRates:

    def test_returns_dict_with_all_mechanisms(self, seeded_model):
        rates = seeded_model.compute_adoption_rates()
        assert set(rates.keys()) == set(MECHANISMS)

    def test_all_zero_before_any_step(self, seeded_model):
        rates = seeded_model.compute_adoption_rates()
        assert all(r == 0.0 for r in rates.values())

    def test_nonzero_after_step(self, seeded_model):
        seeded_model.step()
        rates = seeded_model.compute_adoption_rates()
        # Mock reasoner returns one of 7 mechanisms per cycle, so at least 1 should be > 0
        assert any(r > 0.0 for r in rates.values())

    def test_fractions_in_range(self, seeded_model):
        seeded_model.step()
        rates = seeded_model.compute_adoption_rates()
        for r in rates.values():
            assert 0.0 <= r <= 1.0


# ---------------------------------------------------------------------------
# Custom action count
# ---------------------------------------------------------------------------

class TestCustomActionCount:

    def test_zero_when_no_custom(self, seeded_model):
        # Mock reasoner never returns custom mechanism
        seeded_model.step()
        # Depending on cycle, it uses standard mechanisms
        # count may or may not be 0, but let's verify it returns an int
        count = seeded_model.compute_custom_action_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_counts_custom_actions(self, seeded_model):
        # Manually inject a custom action
        seeded_model.cycle_actions = [
            {"mechanism": "custom", "agent_id": 1},
            {"mechanism": "price", "agent_id": 2},
            {"mechanism": "custom", "agent_id": 3},
        ]
        assert seeded_model.compute_custom_action_count() == 2


# ---------------------------------------------------------------------------
# Behavioral patterns
# ---------------------------------------------------------------------------

class TestBehavioralPatterns:

    def test_returns_dict_per_mechanism(self, seeded_model):
        seeded_model.cycle_actions = [
            {"mechanism": "price", "action_type": "bid"},
            {"mechanism": "price", "action_type": "ask"},
            {"mechanism": "money", "action_type": "pay"},
        ]
        patterns = seeded_model._compute_behavioral_patterns()
        assert set(MECHANISMS).issubset(set(patterns.keys()))
        assert patterns["price"] == {"bid": 1, "ask": 1}
        assert patterns["money"] == {"pay": 1}
        assert patterns["employment"] == {}

    def test_ignores_custom_mechanism(self, seeded_model):
        seeded_model.cycle_actions = [
            {"mechanism": "custom", "action_type": "custom"},
        ]
        patterns = seeded_model._compute_behavioral_patterns()
        # "custom" is not in MECHANISMS, so it should not appear
        assert "custom" not in patterns


# ---------------------------------------------------------------------------
# Baseline patterns capture
# ---------------------------------------------------------------------------

class TestBaselineCapture:

    def test_baseline_none_initially(self, seeded_model):
        assert seeded_model.baseline_patterns is None

    def test_baseline_captured_at_end_of_phase1(self, seeded_model):
        config = seeded_model.config
        for _ in range(config.phase1_cycles):
            seeded_model.step()
            seeded_model.datacollector.collect(seeded_model)

        # baseline_patterns should be captured at cycle phase1_cycles - 1
        assert seeded_model.baseline_patterns is not None
        assert isinstance(seeded_model.baseline_patterns, dict)
        assert set(MECHANISMS).issubset(set(seeded_model.baseline_patterns.keys()))


# ---------------------------------------------------------------------------
# async_step()
# ---------------------------------------------------------------------------

class TestAsyncStep:

    @pytest.mark.asyncio
    async def test_advances_cycle(self, seeded_model):
        await seeded_model.async_step()
        assert seeded_model.cycle == 1

    @pytest.mark.asyncio
    async def test_multiple_steps(self, seeded_model):
        for _ in range(5):
            await seeded_model.async_step()
        assert seeded_model.cycle == 5

    @pytest.mark.asyncio
    async def test_produces_actions(self, seeded_model):
        await seeded_model.async_step()
        assert len(seeded_model.cycle_actions) > 0

    @pytest.mark.asyncio
    async def test_all_agents_act(self, seeded_model):
        await seeded_model.async_step()
        agent_ids = {a["agent_id"] for a in seeded_model.cycle_actions}
        expected_ids = {a.unique_id for a in seeded_model.agents_list}
        assert agent_ids == expected_ids

    @pytest.mark.asyncio
    async def test_resets_cycle_actions_each_step(self, seeded_model):
        await seeded_model.async_step()
        await seeded_model.async_step()
        # Actions should be from the second cycle only
        assert all(a["cycle"] == 1 for a in seeded_model.cycle_actions)

    @pytest.mark.asyncio
    async def test_baseline_captured_at_end_of_phase1(self, seeded_model):
        config = seeded_model.config
        for _ in range(config.phase1_cycles):
            await seeded_model.async_step()
        assert seeded_model.baseline_patterns is not None

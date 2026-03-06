"""
@file test_coordination_efficiency.py
@description Tests for _compute_coordination_efficiency in src/collector.py.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-06
@changelog
- 2026-03-06: v1.0.0 - Initial creation
"""

from __future__ import annotations

import math

import pytest

from src.collector import _compute_coordination_efficiency


class TestComputeCoordinationEfficiency:

    def test_empty_actions_returns_1(self):
        assert _compute_coordination_efficiency([], 7) == 1.0

    def test_single_good_returns_0(self):
        """All actions target the same good: entropy=0, ratio=0."""
        actions = [
            {"target_good": "food_shelter"},
            {"target_good": "food_shelter"},
            {"target_good": "food_shelter"},
        ]
        result = _compute_coordination_efficiency(actions, 7)
        assert result == pytest.approx(0.0, abs=1e-9)

    def test_uniform_distribution_returns_near_1(self):
        """Each of 7 goods appears exactly once: max entropy."""
        goods = [
            "food_shelter", "manufactured", "information",
            "attention", "status", "location", "unique_experiences",
        ]
        actions = [{"target_good": g} for g in goods]
        result = _compute_coordination_efficiency(actions, 7)
        assert result == pytest.approx(1.0, abs=1e-9)

    def test_mixed_distribution_between_0_and_1(self):
        """Non-uniform distribution gives entropy ratio between 0 and 1."""
        actions = [
            {"target_good": "food_shelter"},
            {"target_good": "food_shelter"},
            {"target_good": "food_shelter"},
            {"target_good": "manufactured"},
        ]
        result = _compute_coordination_efficiency(actions, 7)
        assert 0.0 < result < 1.0

    def test_n_goods_1_returns_1(self):
        """Single good type in the simulation: always returns 1.0."""
        actions = [{"target_good": "food_shelter"}]
        result = _compute_coordination_efficiency(actions, 1)
        assert result == 1.0

    def test_actions_without_target_good_returns_1(self):
        """Actions with no target_good key are skipped; empty counts -> 1.0."""
        actions = [
            {"mechanism": "price", "reasoning": "test"},
            {"mechanism": "money"},
        ]
        result = _compute_coordination_efficiency(actions, 7)
        assert result == 1.0

    def test_two_goods_equal_distribution(self):
        """2 goods equally distributed among 7 possible goods."""
        actions = [
            {"target_good": "food_shelter"},
            {"target_good": "manufactured"},
        ]
        result = _compute_coordination_efficiency(actions, 7)
        # actual_entropy = log2(2) = 1.0, max_entropy = log2(7) ~ 2.807
        expected = math.log2(2) / math.log2(7)
        assert result == pytest.approx(expected, abs=1e-9)

    def test_none_target_good_ignored(self):
        """Actions where target_good is None should be skipped."""
        actions = [
            {"target_good": None},
            {"target_good": "food_shelter"},
            {"target_good": "food_shelter"},
        ]
        result = _compute_coordination_efficiency(actions, 7)
        # Only food_shelter counts: single good -> 0.0
        assert result == pytest.approx(0.0, abs=1e-9)

    def test_result_in_valid_range(self):
        """Any input should produce a result in [0.0, 1.0]."""
        import random
        rng = random.Random(42)
        goods = ["food_shelter", "manufactured", "information", "attention",
                 "status", "location", "unique_experiences"]
        for _ in range(50):
            n_actions = rng.randint(1, 20)
            actions = [{"target_good": rng.choice(goods)} for _ in range(n_actions)]
            result = _compute_coordination_efficiency(actions, 7)
            assert 0.0 <= result <= 1.0

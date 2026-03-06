"""
@file test_config.py
@description Tests for SimConfig dataclass and scarcity_at() function.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-05
@changelog
- 2026-03-05: v1.0.0 - Initial creation
"""

from __future__ import annotations

import math

import pytest

from src.config import MECHANISMS, SCARCITY_CURVES, VERDICTS, SimConfig, scarcity_at


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

class TestSimConfigDefaults:

    def test_default_transition_rate(self):
        c = SimConfig()
        assert c.transition_rate == 25

    def test_default_scarcity_curve(self):
        c = SimConfig()
        assert c.scarcity_curve == "linear"

    def test_default_random_seed(self):
        c = SimConfig()
        assert c.random_seed == 42

    def test_default_n_agents(self):
        c = SimConfig()
        assert c.n_agents == 100

    def test_default_phase1_cycles(self):
        c = SimConfig()
        assert c.phase1_cycles == 200

    def test_default_phase3_cycles(self):
        c = SimConfig()
        assert c.phase3_cycles == 200

    def test_default_phase4_cycles(self):
        c = SimConfig()
        assert c.phase4_cycles == 50

    def test_frozen(self):
        c = SimConfig()
        with pytest.raises(AttributeError):
            c.transition_rate = 10  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

class TestConstants:

    def test_mechanisms_count(self):
        assert len(MECHANISMS) == 7

    def test_mechanisms_are_strings(self):
        assert all(isinstance(m, str) for m in MECHANISMS)

    def test_scarcity_curves(self):
        assert set(SCARCITY_CURVES) == {"linear", "exponential", "step"}

    def test_verdicts_count(self):
        assert len(VERDICTS) == 6


# ---------------------------------------------------------------------------
# Derived properties
# ---------------------------------------------------------------------------

class TestDerivedProperties:

    def test_phase2_cycles_equals_transition_rate(self):
        c = SimConfig(transition_rate=30)
        assert c.phase2_cycles == 30

    def test_total_cycles(self):
        c = SimConfig(phase1_cycles=10, transition_rate=5, phase3_cycles=10, phase4_cycles=3)
        assert c.total_cycles == 10 + 5 + 10 + 3

    def test_total_cycles_default(self):
        c = SimConfig()
        assert c.total_cycles == 200 + 25 + 200 + 50


# ---------------------------------------------------------------------------
# scarcity_at() — module-level function
# ---------------------------------------------------------------------------

class TestScarcityAt:

    def test_linear_start(self):
        assert scarcity_at(0, 100, "linear") == 1.0

    def test_linear_end(self):
        assert scarcity_at(100, 100, "linear") == 0.0

    def test_linear_midpoint(self):
        assert scarcity_at(50, 100, "linear") == pytest.approx(0.5)

    def test_exponential_start(self):
        assert scarcity_at(0, 100, "exponential") == pytest.approx(1.0)

    def test_exponential_decays(self):
        # At halfway, exp(-5 * 0.5) = exp(-2.5)
        assert scarcity_at(50, 100, "exponential") == pytest.approx(math.exp(-2.5))

    def test_exponential_near_zero_at_end(self):
        val = scarcity_at(100, 100, "exponential")
        assert val < 0.01

    def test_step_before_end(self):
        assert scarcity_at(0, 100, "step") == 1.0
        assert scarcity_at(50, 100, "step") == 1.0
        assert scarcity_at(99, 100, "step") == 1.0

    def test_step_at_end(self):
        assert scarcity_at(100, 100, "step") == 0.0

    def test_invalid_curve_raises(self):
        with pytest.raises(ValueError, match="Unknown scarcity curve"):
            scarcity_at(0, 100, "logistic")


# ---------------------------------------------------------------------------
# phase_at()
# ---------------------------------------------------------------------------

class TestPhaseAt:

    @pytest.fixture()
    def config(self):
        return SimConfig(phase1_cycles=10, transition_rate=5, phase3_cycles=10, phase4_cycles=3)

    def test_baseline_start(self, config):
        assert config.phase_at(0) == "baseline"

    def test_baseline_end(self, config):
        assert config.phase_at(9) == "baseline"

    def test_transition_start(self, config):
        assert config.phase_at(10) == "transition"

    def test_transition_end(self, config):
        assert config.phase_at(14) == "transition"

    def test_steady_state_start(self, config):
        assert config.phase_at(15) == "steady_state"

    def test_steady_state_end(self, config):
        assert config.phase_at(24) == "steady_state"

    def test_reversibility_start(self, config):
        assert config.phase_at(25) == "reversibility"

    def test_reversibility_end(self, config):
        assert config.phase_at(27) == "reversibility"


# ---------------------------------------------------------------------------
# material_scarcity_at()
# ---------------------------------------------------------------------------

class TestMaterialScarcityAt:

    @pytest.fixture()
    def config(self):
        return SimConfig(
            phase1_cycles=10, transition_rate=10, phase3_cycles=10, phase4_cycles=3,
            scarcity_curve="linear",
        )

    def test_baseline_is_1(self, config):
        assert config.material_scarcity_at(0) == 1.0
        assert config.material_scarcity_at(9) == 1.0

    def test_transition_decreases(self, config):
        # Cycle 10 is t=0 in Phase 2, scarcity_at(0, 10, linear) = 1.0
        assert config.material_scarcity_at(10) == 1.0
        # Cycle 15 is t=5, scarcity_at(5, 10, linear) = 0.5
        assert config.material_scarcity_at(15) == pytest.approx(0.5)

    def test_steady_state_is_0(self, config):
        assert config.material_scarcity_at(20) == 0.0
        assert config.material_scarcity_at(29) == 0.0

    def test_reversibility_is_half(self, config):
        assert config.material_scarcity_at(30) == 0.5
        assert config.material_scarcity_at(32) == 0.5

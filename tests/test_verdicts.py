"""
@file test_verdicts.py
@description Tests for the verdict classification engine (src/verdicts.py).
    Covers all 6 verdict paths and helper functions with synthetic DataFrames.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-06
@changelog
- 2026-03-06: v1.0.0 - Initial creation
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.config import MECHANISMS, SimConfig, VERDICTS
from src.verdicts import (
    _check_consecutive_above,
    _check_consecutive_below,
    _compute_goods_domain_jaccard,
    classify_all_mechanisms,
    classify_mechanism,
)


# ---------------------------------------------------------------------------
# Shared config for verdict tests — small values for speed
# ---------------------------------------------------------------------------

@pytest.fixture()
def verdict_config() -> SimConfig:
    return SimConfig(
        n_agents=5,
        phase1_cycles=5,
        phase3_cycles=25,
        phase4_cycles=15,
        transition_rate=5,
        collapse_threshold=0.05,
        collapse_sustained_n=20,
        efficiency_idle_band=(0.9, 1.1),
        behavioral_pattern_threshold=0.6,
        recovery_adoption_threshold=0.10,
        recovery_sustained_n=10,
        goods_domain_jaccard_threshold=0.7,
    )


# ---------------------------------------------------------------------------
# DataFrame builder helpers
# ---------------------------------------------------------------------------

COLUMNS = [
    "cycle", "phase", "mechanism", "adoption_rate",
    "coordination_efficiency", "behavioral_pattern_score",
]


def _build_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=COLUMNS)


def _phase_rows(
    mechanism: str,
    phase: str,
    n_cycles: int,
    start_cycle: int,
    adoption: float,
    efficiency: float,
    bps: float,
) -> list[dict]:
    """Generate n_cycles rows for a single mechanism/phase combination."""
    return [
        {
            "cycle": start_cycle + i,
            "phase": phase,
            "mechanism": mechanism,
            "adoption_rate": adoption,
            "coordination_efficiency": efficiency,
            "behavioral_pattern_score": bps,
        }
        for i in range(n_cycles)
    ]


# ---------------------------------------------------------------------------
# Helper function tests: _check_consecutive_below
# ---------------------------------------------------------------------------

class TestCheckConsecutiveBelow:

    def test_true_when_consecutive_run_exists(self):
        series = pd.Series([0.01, 0.02, 0.03, 0.04, 0.01])
        assert _check_consecutive_below(series, 0.05, 5) is True

    def test_false_when_run_interrupted(self):
        series = pd.Series([0.01, 0.02, 0.06, 0.03, 0.04])
        assert _check_consecutive_below(series, 0.05, 4) is False

    def test_false_when_series_too_short(self):
        series = pd.Series([0.01, 0.02])
        assert _check_consecutive_below(series, 0.05, 5) is False

    def test_exact_boundary_not_below(self):
        """Values exactly AT threshold are not below it."""
        series = pd.Series([0.05, 0.05, 0.05, 0.05, 0.05])
        assert _check_consecutive_below(series, 0.05, 5) is False

    def test_empty_series(self):
        series = pd.Series([], dtype=float)
        assert _check_consecutive_below(series, 0.05, 1) is False

    def test_run_at_end_of_series(self):
        series = pd.Series([0.10, 0.10, 0.01, 0.01, 0.01])
        assert _check_consecutive_below(series, 0.05, 3) is True

    def test_run_at_beginning_of_series(self):
        series = pd.Series([0.01, 0.01, 0.01, 0.10, 0.10])
        assert _check_consecutive_below(series, 0.05, 3) is True

    def test_n_equals_1(self):
        series = pd.Series([0.10, 0.01, 0.10])
        assert _check_consecutive_below(series, 0.05, 1) is True


# ---------------------------------------------------------------------------
# Helper function tests: _check_consecutive_above
# ---------------------------------------------------------------------------

class TestCheckConsecutiveAbove:

    def test_true_when_consecutive_run_exists(self):
        series = pd.Series([0.15, 0.20, 0.25, 0.30, 0.10])
        assert _check_consecutive_above(series, 0.10, 4) is True

    def test_false_when_run_interrupted(self):
        series = pd.Series([0.15, 0.20, 0.05, 0.15, 0.20])
        assert _check_consecutive_above(series, 0.10, 4) is False

    def test_false_when_series_too_short(self):
        series = pd.Series([0.15])
        assert _check_consecutive_above(series, 0.10, 3) is False

    def test_exact_boundary_is_above(self):
        """Values exactly AT threshold satisfy >= condition."""
        series = pd.Series([0.10, 0.10, 0.10])
        assert _check_consecutive_above(series, 0.10, 3) is True

    def test_empty_series(self):
        series = pd.Series([], dtype=float)
        assert _check_consecutive_above(series, 0.10, 1) is False

    def test_n_equals_1(self):
        series = pd.Series([0.05, 0.15, 0.05])
        assert _check_consecutive_above(series, 0.10, 1) is True


# ---------------------------------------------------------------------------
# Helper function tests: _compute_goods_domain_jaccard
# ---------------------------------------------------------------------------

class TestGoodsDomainJaccard:

    def test_identical_sets_returns_1(self):
        actions1 = [{"target_good": "food_shelter"}, {"target_good": "manufactured"}]
        actions2 = [{"target_good": "food_shelter"}, {"target_good": "manufactured"}]
        assert _compute_goods_domain_jaccard(actions1, actions2) == 1.0

    def test_disjoint_sets_returns_0(self):
        actions1 = [{"target_good": "food_shelter"}]
        actions2 = [{"target_good": "attention"}]
        assert _compute_goods_domain_jaccard(actions1, actions2) == 0.0

    def test_partial_overlap(self):
        actions1 = [{"target_good": "food_shelter"}, {"target_good": "manufactured"}]
        actions2 = [{"target_good": "manufactured"}, {"target_good": "attention"}]
        # intersection={manufactured}, union={food_shelter, manufactured, attention}
        assert _compute_goods_domain_jaccard(actions1, actions2) == pytest.approx(1 / 3)

    def test_both_empty_returns_1(self):
        assert _compute_goods_domain_jaccard([], []) == 1.0

    def test_one_empty_returns_0(self):
        actions1 = [{"target_good": "food_shelter"}]
        assert _compute_goods_domain_jaccard(actions1, []) == 0.0
        assert _compute_goods_domain_jaccard([], actions1) == 0.0

    def test_actions_without_target_good_ignored(self):
        actions1 = [{"target_good": "food_shelter"}, {"reasoning": "no good here"}]
        actions2 = [{"target_good": "food_shelter"}]
        assert _compute_goods_domain_jaccard(actions1, actions2) == 1.0

    def test_none_target_good_ignored(self):
        actions1 = [{"target_good": None}, {"target_good": "food_shelter"}]
        actions2 = [{"target_good": "food_shelter"}]
        assert _compute_goods_domain_jaccard(actions1, actions2) == 1.0


# ---------------------------------------------------------------------------
# Verdict path tests: classify_mechanism
# ---------------------------------------------------------------------------

class TestVerdictCollapse:
    """COLLAPSE: adoption < 0.05 for 20 consecutive cycles in Phase 3, no recovery in Phase 4."""

    def test_collapse_verdict(self, verdict_config):
        phase3 = _build_df(_phase_rows("price", "steady_state", 25, 10, 0.02, 0.5, 0.3))
        phase4 = _build_df(_phase_rows("price", "reversibility", 15, 40, 0.03, 0.5, 0.3))
        phase1 = _build_df(_phase_rows("price", "baseline", 5, 0, 0.20, 1.0, 0.8))

        result = classify_mechanism("price", phase3, phase4, phase1, verdict_config)

        assert result["verdict"] == "COLLAPSE"
        assert result["collapse_triggered"] is True
        assert result["recovery_triggered"] is False

    def test_collapse_not_triggered_if_adoption_above_threshold(self, verdict_config):
        phase3 = _build_df(_phase_rows("price", "steady_state", 25, 10, 0.10, 1.0, 0.8))
        phase4 = _build_df(_phase_rows("price", "reversibility", 15, 40, 0.10, 1.0, 0.8))
        phase1 = _build_df(_phase_rows("price", "baseline", 5, 0, 0.20, 1.0, 0.8))

        result = classify_mechanism("price", phase3, phase4, phase1, verdict_config)

        assert result["collapse_triggered"] is False
        assert result["verdict"] != "COLLAPSE"


class TestVerdictPersistDormant:
    """PERSIST_DORMANT: collapse in Phase 3, but recovery (>= 0.10 for 10 cycles) in Phase 4."""

    def test_persist_dormant_verdict(self, verdict_config):
        phase3 = _build_df(_phase_rows("money", "steady_state", 25, 10, 0.02, 0.5, 0.3))
        phase4 = _build_df(_phase_rows("money", "reversibility", 15, 40, 0.15, 0.5, 0.3))
        phase1 = _build_df(_phase_rows("money", "baseline", 5, 0, 0.20, 1.0, 0.8))

        result = classify_mechanism("money", phase3, phase4, phase1, verdict_config)

        assert result["verdict"] == "PERSIST_DORMANT"
        assert result["collapse_triggered"] is True
        assert result["recovery_triggered"] is True


class TestVerdictPersistIdle:
    """PERSIST_IDLE: no collapse, efficiency in [0.9, 1.1]."""

    def test_persist_idle_verdict(self, verdict_config):
        phase3 = _build_df(_phase_rows("property", "steady_state", 25, 10, 0.20, 1.0, 0.8))
        phase4 = _build_df(_phase_rows("property", "reversibility", 15, 40, 0.20, 1.0, 0.8))
        phase1 = _build_df(_phase_rows("property", "baseline", 5, 0, 0.20, 1.0, 0.8))

        result = classify_mechanism("property", phase3, phase4, phase1, verdict_config)

        assert result["verdict"] == "PERSIST_IDLE"
        assert result["collapse_triggered"] is False

    def test_idle_at_lower_boundary(self, verdict_config):
        phase3 = _build_df(_phase_rows("property", "steady_state", 25, 10, 0.20, 0.9, 0.8))
        phase4 = _build_df(_phase_rows("property", "reversibility", 15, 40, 0.20, 0.9, 0.8))
        phase1 = _build_df(_phase_rows("property", "baseline", 5, 0, 0.20, 1.0, 0.8))

        result = classify_mechanism("property", phase3, phase4, phase1, verdict_config)

        assert result["verdict"] == "PERSIST_IDLE"

    def test_idle_at_upper_boundary(self, verdict_config):
        phase3 = _build_df(_phase_rows("property", "steady_state", 25, 10, 0.20, 1.1, 0.8))
        phase4 = _build_df(_phase_rows("property", "reversibility", 15, 40, 0.20, 1.1, 0.8))
        phase1 = _build_df(_phase_rows("property", "baseline", 5, 0, 0.20, 1.0, 0.8))

        result = classify_mechanism("property", phase3, phase4, phase1, verdict_config)

        assert result["verdict"] == "PERSIST_IDLE"


class TestVerdictPersistActive:
    """PERSIST_ACTIVE: no collapse, efficiency > 1.1, BPS >= 0.6, Jaccard >= 0.7."""

    def test_persist_active_verdict(self, verdict_config):
        """Default Jaccard is 1.0 (same domain) when no raw actions provided."""
        phase3 = _build_df(_phase_rows("employment", "steady_state", 25, 10, 0.30, 1.5, 0.8))
        phase4 = _build_df(_phase_rows("employment", "reversibility", 15, 40, 0.30, 1.5, 0.8))
        phase1 = _build_df(_phase_rows("employment", "baseline", 5, 0, 0.25, 1.0, 0.8))

        result = classify_mechanism("employment", phase3, phase4, phase1, verdict_config)

        assert result["verdict"] == "PERSIST_ACTIVE"
        assert result["collapse_triggered"] is False
        assert result["goods_domain_jaccard"] == 1.0  # default


class TestVerdictRepurpose:
    """REPURPOSE: no collapse, efficiency > 1.1, BPS >= 0.6, Jaccard < 0.7.

    Since classify_mechanism defaults Jaccard to 1.0, REPURPOSE requires
    raw_actions via classify_all_mechanisms. We test that path here.
    """

    def test_repurpose_via_classify_all(self, verdict_config):
        """Provide raw_actions with low Jaccard to trigger REPURPOSE."""
        rows = []
        for mech in MECHANISMS:
            rows.extend(_phase_rows(mech, "baseline", 5, 0, 0.25, 1.0, 0.8))
            rows.extend(_phase_rows(mech, "steady_state", 25, 10, 0.30, 1.5, 0.8))
            rows.extend(_phase_rows(mech, "reversibility", 15, 40, 0.30, 1.5, 0.8))

        cycle_df = _build_df(rows)

        # Provide raw actions where "price" has disjoint goods domains
        raw_actions = {
            "price": {
                "baseline": [{"target_good": "food_shelter"}, {"target_good": "manufactured"}],
                "steady_state": [{"target_good": "attention"}, {"target_good": "status"}],
            }
        }

        result_df = classify_all_mechanisms(cycle_df, verdict_config, raw_actions=raw_actions)
        price_row = result_df[result_df["mechanism"] == "price"].iloc[0]

        assert price_row["verdict"] == "REPURPOSE"
        assert price_row["goods_domain_jaccard"] == 0.0


class TestVerdictNovelMechanism:
    """NOVEL_MECHANISM: no collapse, efficiency > 1.1, BPS < 0.6."""

    def test_novel_mechanism_verdict(self, verdict_config):
        phase3 = _build_df(_phase_rows("taxation", "steady_state", 25, 10, 0.30, 1.5, 0.3))
        phase4 = _build_df(_phase_rows("taxation", "reversibility", 15, 40, 0.30, 1.5, 0.3))
        phase1 = _build_df(_phase_rows("taxation", "baseline", 5, 0, 0.25, 1.0, 0.8))

        result = classify_mechanism("taxation", phase3, phase4, phase1, verdict_config)

        assert result["verdict"] == "NOVEL_MECHANISM"
        assert result["behavioral_pattern_score"] < verdict_config.behavioral_pattern_threshold


# ---------------------------------------------------------------------------
# classify_all_mechanisms tests
# ---------------------------------------------------------------------------

class TestClassifyAllMechanisms:

    def test_returns_7_rows(self, verdict_config):
        """One row per mechanism."""
        rows = []
        for mech in MECHANISMS:
            rows.extend(_phase_rows(mech, "baseline", 5, 0, 0.20, 1.0, 0.8))
            rows.extend(_phase_rows(mech, "steady_state", 25, 10, 0.20, 1.0, 0.8))
            rows.extend(_phase_rows(mech, "reversibility", 15, 40, 0.20, 1.0, 0.8))

        cycle_df = _build_df(rows)
        result_df = classify_all_mechanisms(cycle_df, verdict_config)

        assert len(result_df) == 7
        assert set(result_df["mechanism"]) == set(MECHANISMS)

    def test_all_verdicts_are_valid(self, verdict_config):
        rows = []
        for mech in MECHANISMS:
            rows.extend(_phase_rows(mech, "baseline", 5, 0, 0.20, 1.0, 0.8))
            rows.extend(_phase_rows(mech, "steady_state", 25, 10, 0.20, 1.0, 0.8))
            rows.extend(_phase_rows(mech, "reversibility", 15, 40, 0.20, 1.0, 0.8))

        cycle_df = _build_df(rows)
        result_df = classify_all_mechanisms(cycle_df, verdict_config)

        for verdict in result_df["verdict"]:
            assert verdict in VERDICTS

    def test_output_columns_match_schema(self, verdict_config):
        rows = []
        for mech in MECHANISMS:
            rows.extend(_phase_rows(mech, "baseline", 5, 0, 0.20, 1.0, 0.8))
            rows.extend(_phase_rows(mech, "steady_state", 25, 10, 0.20, 1.0, 0.8))
            rows.extend(_phase_rows(mech, "reversibility", 15, 40, 0.20, 1.0, 0.8))

        cycle_df = _build_df(rows)
        result_df = classify_all_mechanisms(cycle_df, verdict_config)

        expected_columns = [
            "run_id", "seed", "transition_rate", "scarcity_curve", "n_agents",
            "mechanism", "verdict",
            "collapse_triggered", "recovery_triggered",
            "mean_adoption_phase3", "mean_efficiency_phase3",
            "behavioral_pattern_score", "goods_domain_jaccard",
            "notes",
        ]
        assert list(result_df.columns) == expected_columns

    def test_metadata_propagated(self, verdict_config):
        rows = []
        for mech in MECHANISMS:
            rows.extend(_phase_rows(mech, "baseline", 5, 0, 0.20, 1.0, 0.8))
            rows.extend(_phase_rows(mech, "steady_state", 25, 10, 0.20, 1.0, 0.8))
            rows.extend(_phase_rows(mech, "reversibility", 15, 40, 0.20, 1.0, 0.8))

        cycle_df = _build_df(rows)
        result_df = classify_all_mechanisms(cycle_df, verdict_config)

        for _, row in result_df.iterrows():
            assert row["run_id"] == verdict_config.random_seed
            assert row["seed"] == verdict_config.random_seed
            assert row["transition_rate"] == verdict_config.transition_rate
            assert row["scarcity_curve"] == verdict_config.scarcity_curve
            assert row["n_agents"] == verdict_config.n_agents


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestVerdictEdgeCases:

    def test_empty_phase3_defaults_to_idle(self, verdict_config):
        phase3 = _build_df([])
        phase4 = _build_df([])
        phase1 = _build_df([])

        result = classify_mechanism("price", phase3, phase4, phase1, verdict_config)
        assert result["verdict"] == "PERSIST_IDLE"

    def test_collapse_exactly_at_sustained_n(self, verdict_config):
        """Exactly 20 cycles below threshold should trigger collapse."""
        phase3_rows = _phase_rows("price", "steady_state", 20, 10, 0.02, 0.5, 0.3)
        # Add 5 more above threshold
        phase3_rows.extend(_phase_rows("price", "steady_state", 5, 30, 0.10, 0.5, 0.3))
        phase3 = _build_df(phase3_rows)
        phase4 = _build_df(_phase_rows("price", "reversibility", 15, 40, 0.03, 0.5, 0.3))
        phase1 = _build_df(_phase_rows("price", "baseline", 5, 0, 0.20, 1.0, 0.8))

        result = classify_mechanism("price", phase3, phase4, phase1, verdict_config)
        assert result["collapse_triggered"] is True

    def test_19_consecutive_below_no_collapse(self, verdict_config):
        """19 cycles below threshold (one short) should NOT trigger collapse."""
        phase3_rows = _phase_rows("price", "steady_state", 19, 10, 0.02, 0.5, 0.3)
        phase3_rows.extend(_phase_rows("price", "steady_state", 6, 29, 0.10, 1.0, 0.8))
        phase3 = _build_df(phase3_rows)
        phase4 = _build_df(_phase_rows("price", "reversibility", 15, 40, 0.10, 1.0, 0.8))
        phase1 = _build_df(_phase_rows("price", "baseline", 5, 0, 0.20, 1.0, 0.8))

        result = classify_mechanism("price", phase3, phase4, phase1, verdict_config)
        assert result["collapse_triggered"] is False

    def test_classify_mechanism_return_structure(self, verdict_config):
        phase3 = _build_df(_phase_rows("price", "steady_state", 25, 10, 0.20, 1.0, 0.8))
        phase4 = _build_df(_phase_rows("price", "reversibility", 15, 40, 0.20, 1.0, 0.8))
        phase1 = _build_df(_phase_rows("price", "baseline", 5, 0, 0.20, 1.0, 0.8))

        result = classify_mechanism("price", phase3, phase4, phase1, verdict_config)

        expected_keys = {
            "mechanism", "verdict", "collapse_triggered", "recovery_triggered",
            "mean_adoption_phase3", "mean_efficiency_phase3",
            "behavioral_pattern_score", "goods_domain_jaccard", "notes",
        }
        assert set(result.keys()) == expected_keys
        assert isinstance(result["mechanism"], str)
        assert isinstance(result["verdict"], str)
        assert isinstance(result["collapse_triggered"], bool)
        assert isinstance(result["recovery_triggered"], bool)
        assert isinstance(result["mean_adoption_phase3"], float)
        assert isinstance(result["mean_efficiency_phase3"], float)
        assert isinstance(result["notes"], str)

"""
@file test_retroanalysis.py
@description Tests for the retroanalysis module (src/retroanalysis.py).
    Covers replacement chain tracing and information structure classification.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-06
@changelog
- 2026-03-06: v1.0.0 - Initial creation
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.config import MECHANISMS, SimConfig
from src.retroanalysis import information_structure_check, trace_replacement_chains


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------

@pytest.fixture()
def retro_config() -> SimConfig:
    return SimConfig(
        n_agents=5,
        phase1_cycles=5,
        phase3_cycles=25,
        phase4_cycles=15,
        transition_rate=5,
        collapse_threshold=0.05,
        collapse_sustained_n=20,
    )


# ---------------------------------------------------------------------------
# DataFrame builder
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
    efficiency: float = 1.0,
    bps: float = 0.8,
) -> list[dict]:
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


def _variable_adoption_rows(
    mechanism: str,
    phase: str,
    start_cycle: int,
    adoptions: list[float],
) -> list[dict]:
    """Create rows with varying adoption rates per cycle."""
    return [
        {
            "cycle": start_cycle + i,
            "phase": phase,
            "mechanism": mechanism,
            "adoption_rate": a,
            "coordination_efficiency": 1.0,
            "behavioral_pattern_score": 0.8,
        }
        for i, a in enumerate(adoptions)
    ]


# ---------------------------------------------------------------------------
# trace_replacement_chains tests
# ---------------------------------------------------------------------------

class TestTraceReplacementChains:

    def test_collapsed_mechanism_with_replacement(self, retro_config):
        """When 'price' collapses and 'reputation' gains adoption in the same window."""
        rows = []
        # price collapses: 25 cycles below threshold
        rows.extend(_phase_rows("price", "steady_state", 25, 10, 0.02))
        # reputation gains adoption during same window (increasing)
        rows.extend(_variable_adoption_rows(
            "reputation", "steady_state", 10,
            [0.10 + i * 0.01 for i in range(25)],
        ))
        # Fill other mechanisms with stable data
        for mech in MECHANISMS:
            if mech not in ("price", "reputation"):
                rows.extend(_phase_rows(mech, "steady_state", 25, 10, 0.15))

        cycle_df = _build_df(rows)
        chains = trace_replacement_chains(cycle_df, retro_config)

        assert len(chains) == 1
        assert chains[0]["collapsed_mechanism"] == "price"
        assert chains[0]["collapse_start_cycle"] == 10
        assert len(chains[0]["replacement_mechanisms"]) >= 1

        # reputation should be among replacements
        rep_names = [r["mechanism"] for r in chains[0]["replacement_mechanisms"]]
        assert "reputation" in rep_names

        # Check adoption_increase is positive
        rep_entry = next(r for r in chains[0]["replacement_mechanisms"] if r["mechanism"] == "reputation")
        assert rep_entry["adoption_increase"] > 0

    def test_no_collapsed_mechanisms_returns_empty(self, retro_config):
        """When all mechanisms are above collapse threshold, no chains."""
        rows = []
        for mech in MECHANISMS:
            rows.extend(_phase_rows(mech, "steady_state", 25, 10, 0.20))

        cycle_df = _build_df(rows)
        chains = trace_replacement_chains(cycle_df, retro_config)

        assert chains == []

    def test_collapse_but_no_replacements(self, retro_config):
        """Mechanism collapses but no others gain adoption."""
        rows = []
        # price collapses
        rows.extend(_phase_rows("price", "steady_state", 25, 10, 0.02))
        # All others stable (no increase)
        for mech in MECHANISMS:
            if mech != "price":
                rows.extend(_phase_rows(mech, "steady_state", 25, 10, 0.15))

        cycle_df = _build_df(rows)
        chains = trace_replacement_chains(cycle_df, retro_config)

        assert len(chains) == 1
        assert chains[0]["collapsed_mechanism"] == "price"
        assert chains[0]["replacement_mechanisms"] == []

    def test_empty_steady_state_returns_empty(self, retro_config):
        """No steady_state phase data at all."""
        rows = []
        for mech in MECHANISMS:
            rows.extend(_phase_rows(mech, "baseline", 5, 0, 0.20))

        cycle_df = _build_df(rows)
        chains = trace_replacement_chains(cycle_df, retro_config)

        assert chains == []

    def test_multiple_collapses(self, retro_config):
        """Two mechanisms collapse simultaneously."""
        rows = []
        rows.extend(_phase_rows("price", "steady_state", 25, 10, 0.02))
        rows.extend(_phase_rows("money", "steady_state", 25, 10, 0.01))
        # Rest stable
        for mech in MECHANISMS:
            if mech not in ("price", "money"):
                rows.extend(_phase_rows(mech, "steady_state", 25, 10, 0.15))

        cycle_df = _build_df(rows)
        chains = trace_replacement_chains(cycle_df, retro_config)

        collapsed_mechs = {c["collapsed_mechanism"] for c in chains}
        assert "price" in collapsed_mechs
        assert "money" in collapsed_mechs

    def test_replacements_sorted_by_adoption_increase(self, retro_config):
        """Replacement mechanisms should be sorted by adoption_increase descending."""
        rows = []
        rows.extend(_phase_rows("price", "steady_state", 25, 10, 0.02))
        # reputation gains more than employment
        rows.extend(_variable_adoption_rows(
            "reputation", "steady_state", 10,
            [0.10 + i * 0.02 for i in range(25)],
        ))
        rows.extend(_variable_adoption_rows(
            "employment", "steady_state", 10,
            [0.10 + i * 0.005 for i in range(25)],
        ))
        for mech in MECHANISMS:
            if mech not in ("price", "reputation", "employment"):
                rows.extend(_phase_rows(mech, "steady_state", 25, 10, 0.15))

        cycle_df = _build_df(rows)
        chains = trace_replacement_chains(cycle_df, retro_config)

        assert len(chains) == 1
        replacements = chains[0]["replacement_mechanisms"]
        assert len(replacements) >= 2
        # Should be sorted descending
        increases = [r["adoption_increase"] for r in replacements]
        assert increases == sorted(increases, reverse=True)


# ---------------------------------------------------------------------------
# information_structure_check tests
# ---------------------------------------------------------------------------

class TestInformationStructureCheck:

    def test_discovery_when_phase3_goods_existed_in_phase1(self):
        """Phase 3 uses goods that were already in Phase 1 vocabulary."""
        phase1_actions = [
            {"target_good": "food_shelter", "mechanism": "price"},
            {"target_good": "manufactured", "mechanism": "money"},
            {"target_good": "attention", "mechanism": "reputation"},
        ]
        phase3_actions = [
            {"target_good": "food_shelter"},
            {"target_good": "manufactured"},
        ]

        result = information_structure_check("price", phase1_actions, phase3_actions)
        assert result == "discovery"

    def test_labeling_when_over_30_percent_novel(self):
        """More than 30% of Phase 3 goods are completely absent from Phase 1."""
        phase1_actions = [
            {"target_good": "food_shelter"},
            {"target_good": "manufactured"},
        ]
        # 3 out of 4 = 75% novel
        phase3_actions = [
            {"target_good": "food_shelter"},  # known
            {"target_good": "quantum_compute"},  # novel
            {"target_good": "neural_bandwidth"},  # novel
            {"target_good": "digital_trust"},  # novel
        ]

        result = information_structure_check("reputation", phase1_actions, phase3_actions)
        assert result == "labeling"

    def test_discovery_with_empty_phase3_actions(self):
        """Empty Phase 3 actions defaults to discovery."""
        phase1_actions = [{"target_good": "food_shelter"}]
        phase3_actions = []

        result = information_structure_check("price", phase1_actions, phase3_actions)
        assert result == "discovery"

    def test_discovery_at_exactly_30_percent_novel(self):
        """Exactly 30% novel does NOT trigger labeling (>30% required)."""
        phase1_actions = [
            {"target_good": "food_shelter"},
            {"target_good": "manufactured"},
            {"target_good": "attention"},
        ]
        # 3 out of 10 = 30% novel
        phase3_actions = (
            [{"target_good": "food_shelter"}] * 7
            + [{"target_good": "quantum_compute"}] * 3
        )

        result = information_structure_check("price", phase1_actions, phase3_actions)
        assert result == "discovery"

    def test_labeling_with_all_novel_goods(self):
        """100% novel goods in Phase 3."""
        phase1_actions = [{"target_good": "food_shelter"}]
        phase3_actions = [
            {"target_good": "quantum_compute"},
            {"target_good": "neural_bandwidth"},
        ]

        result = information_structure_check("price", phase1_actions, phase3_actions)
        assert result == "labeling"

    def test_discovery_with_empty_phase1_and_phase3(self):
        """Both phases have no actions with target_good."""
        result = information_structure_check("price", [], [])
        assert result == "discovery"

    def test_actions_without_target_good_are_ignored(self):
        """Actions missing target_good should not count."""
        phase1_actions = [{"target_good": "food_shelter"}, {"reasoning": "no good"}]
        phase3_actions = [{"target_good": "food_shelter"}, {"mechanism": "price"}]

        result = information_structure_check("price", phase1_actions, phase3_actions)
        assert result == "discovery"

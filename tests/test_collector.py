"""
@file test_collector.py
@description Tests for DataCollector, cosine similarity, and CSV export functions.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-05
@changelog
- 2026-03-05: v1.0.0 - Initial creation
"""

from __future__ import annotations

import math

import pytest

from src.collector import (
    _cosine_similarity,
    create_collector,
    export_cycle_data,
    export_novel_actions,
)
from src.config import MECHANISMS


# ---------------------------------------------------------------------------
# _cosine_similarity
# ---------------------------------------------------------------------------

class TestCosineSimilarity:

    def test_identical_vectors(self):
        a = {"x": 3, "y": 4}
        assert _cosine_similarity(a, a) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = {"x": 1, "y": 0}
        b = {"x": 0, "y": 1}
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_empty_first(self):
        assert _cosine_similarity({}, {"x": 1}) == 0.0

    def test_empty_second(self):
        assert _cosine_similarity({"x": 1}, {}) == 0.0

    def test_both_empty(self):
        assert _cosine_similarity({}, {}) == 0.0

    def test_partial_overlap(self):
        a = {"x": 1, "y": 2}
        b = {"x": 1, "z": 2}
        # dot = 1*1 + 0 + 0 = 1
        # mag_a = sqrt(1+4) = sqrt(5), mag_b = sqrt(1+4) = sqrt(5)
        expected = 1.0 / (math.sqrt(5) * math.sqrt(5))
        assert _cosine_similarity(a, b) == pytest.approx(expected)

    def test_proportional_vectors(self):
        a = {"x": 1, "y": 2}
        b = {"x": 2, "y": 4}
        assert _cosine_similarity(a, b) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# create_collector
# ---------------------------------------------------------------------------

class TestCreateCollector:

    def test_returns_datacollector(self):
        from mesa import DataCollector
        dc = create_collector()
        assert isinstance(dc, DataCollector)


# ---------------------------------------------------------------------------
# export_cycle_data
# ---------------------------------------------------------------------------

EXPECTED_COLUMNS = {
    "run_id", "seed", "transition_rate", "scarcity_curve", "n_agents",
    "cycle", "phase", "material_scarcity", "mechanism",
    "adoption_rate", "coordination_efficiency", "behavioral_pattern_score",
    "custom_action_count",
}


class TestExportCycleData:

    def test_writes_csv(self, seeded_model, tmp_output_dir):
        seeded_model.step()
        seeded_model.datacollector.collect(seeded_model)

        export_cycle_data(seeded_model, tmp_output_dir)
        csv_path = tmp_output_dir / "cycle_data.csv"
        assert csv_path.exists()

    def test_csv_has_expected_columns(self, seeded_model, tmp_output_dir):
        seeded_model.step()
        seeded_model.datacollector.collect(seeded_model)

        df = export_cycle_data(seeded_model, tmp_output_dir)
        assert EXPECTED_COLUMNS == set(df.columns)

    def test_all_mechanisms_present(self, seeded_model, tmp_output_dir):
        seeded_model.step()
        seeded_model.datacollector.collect(seeded_model)

        df = export_cycle_data(seeded_model, tmp_output_dir)
        mechanisms_in_csv = set(df["mechanism"].unique())
        assert mechanisms_in_csv == set(MECHANISMS)

    def test_multiple_cycles(self, seeded_model, tmp_output_dir):
        for _ in range(3):
            seeded_model.step()
            seeded_model.datacollector.collect(seeded_model)

        df = export_cycle_data(seeded_model, tmp_output_dir)
        # 3 cycles * 7 mechanisms = 21 rows
        assert len(df) == 3 * len(MECHANISMS)

    def test_creates_output_dir(self, seeded_model, tmp_path):
        nested = tmp_path / "deep" / "nested" / "dir"
        seeded_model.step()
        seeded_model.datacollector.collect(seeded_model)

        export_cycle_data(seeded_model, nested)
        assert (nested / "cycle_data.csv").exists()


# ---------------------------------------------------------------------------
# export_novel_actions
# ---------------------------------------------------------------------------

class TestExportNovelActions:

    def test_writes_csv_empty(self, seeded_model, tmp_output_dir):
        """When no custom actions exist, novel_actions.csv is still created."""
        export_novel_actions(seeded_model, tmp_output_dir)
        csv_path = tmp_output_dir / "novel_actions.csv"
        assert csv_path.exists()

    def test_empty_when_no_custom(self, seeded_model, tmp_output_dir):
        # Run a few steps — mock reasoner uses standard mechanisms
        for _ in range(3):
            seeded_model.step()
            seeded_model.datacollector.collect(seeded_model)

        df = export_novel_actions(seeded_model, tmp_output_dir)
        # Mock reasoner cycles through 7 standard mechanisms, never "custom"
        assert len(df) == 0 or df.empty

    def test_populated_with_custom_actions(self, seeded_model, tmp_output_dir):
        """Manually inject a custom action and verify it appears in the export."""
        agent = seeded_model.agents_list[0]
        agent.action_history.append({
            "mechanism": "custom",
            "action_type": "custom",
            "target_good": "status",
            "counterparty": None,
            "reasoning": "invented barter protocol",
            "details": {},
            "agent_id": agent.unique_id,
            "node_id": agent.node_id,
            "cycle": 0,
        })

        df = export_novel_actions(seeded_model, tmp_output_dir)
        assert len(df) == 1
        assert df.iloc[0]["free_text_description"] == "invented barter protocol"
        assert df.iloc[0]["agent_id"] == agent.unique_id

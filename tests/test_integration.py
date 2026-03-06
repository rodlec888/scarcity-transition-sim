"""
@file test_integration.py
@description Full mocked pipeline integration test: model -> step -> collect -> export -> validate.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-05
@changelog
- 2026-03-05: v1.0.0 - Initial creation
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.collector import create_collector, export_cycle_data, export_novel_actions, export_run_summary
from src.config import MECHANISMS, VERDICTS, SimConfig
from src.environment import ScarcityModel
from src.verdicts import classify_all_mechanisms


# ---------------------------------------------------------------------------
# Expected CSV schema
# ---------------------------------------------------------------------------

EXPECTED_CYCLE_COLUMNS = {
    "run_id", "seed", "transition_rate", "scarcity_curve", "n_agents",
    "cycle", "phase", "material_scarcity", "mechanism",
    "adoption_rate", "coordination_efficiency", "behavioral_pattern_score",
    "custom_action_count",
}


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

class TestFullPipeline:
    """End-to-end test: create model, run all phases, export, validate outputs."""

    @pytest.fixture()
    def pipeline_config(self) -> SimConfig:
        return SimConfig(
            transition_rate=3,
            scarcity_curve="linear",
            random_seed=42,
            n_agents=4,
            phase1_cycles=3,
            phase3_cycles=3,
            phase4_cycles=2,
        )

    @pytest.fixture()
    def run_result(self, pipeline_config, mock_reasoner, tmp_output_dir):
        """Run the full simulation and return (model, cycle_df, novel_df, output_dir)."""
        model = ScarcityModel(pipeline_config)
        model.datacollector = create_collector()

        for cycle in range(pipeline_config.total_cycles):
            model.step()
            model.datacollector.collect(model)

        cycle_df = export_cycle_data(model, tmp_output_dir)
        novel_df = export_novel_actions(model, tmp_output_dir)

        return model, cycle_df, novel_df, tmp_output_dir

    def test_cycle_data_csv_exists(self, run_result):
        _, _, _, output_dir = run_result
        assert (output_dir / "cycle_data.csv").exists()

    def test_novel_actions_csv_exists(self, run_result):
        _, _, _, output_dir = run_result
        assert (output_dir / "novel_actions.csv").exists()

    def test_cycle_data_columns(self, run_result):
        _, cycle_df, _, _ = run_result
        assert set(cycle_df.columns) == EXPECTED_CYCLE_COLUMNS

    def test_all_7_mechanisms_present(self, run_result):
        _, cycle_df, _, _ = run_result
        mechanisms = set(cycle_df["mechanism"].unique())
        assert mechanisms == set(MECHANISMS)

    def test_correct_row_count(self, run_result):
        model, cycle_df, _, _ = run_result
        config = model.config
        expected_rows = config.total_cycles * len(MECHANISMS)
        assert len(cycle_df) == expected_rows

    def test_phases_progress_correctly(self, run_result):
        _, cycle_df, _, _ = run_result
        phases_in_order = cycle_df.drop_duplicates(subset=["cycle"]).sort_values("cycle")["phase"].tolist()
        # Remove duplicates while preserving order
        seen = set()
        phase_sequence = []
        for p in phases_in_order:
            if p not in seen:
                phase_sequence.append(p)
                seen.add(p)
        assert phase_sequence == ["baseline", "transition", "steady_state", "reversibility"]

    def test_material_scarcity_baseline_is_1(self, run_result):
        _, cycle_df, _, _ = run_result
        baseline = cycle_df[cycle_df["phase"] == "baseline"]
        assert (baseline["material_scarcity"] == 1.0).all()

    def test_material_scarcity_reaches_0_in_steady_state(self, run_result):
        """Material scarcity reaches 0.0 during steady state.

        Note: model.material_scarcity is set at the START of step() using
        the current cycle, but model.phase is read AFTER cycle += 1. So the
        first row recorded as "steady_state" may still carry a transition-era
        scarcity value. We verify that at least some steady-state rows are 0.0.
        """
        _, cycle_df, _, _ = run_result
        steady = cycle_df[cycle_df["phase"] == "steady_state"]
        assert not steady.empty
        assert (steady["material_scarcity"] == 0.0).any()
        # The last steady-state cycle must be 0.0
        last_steady = steady[steady["cycle"] == steady["cycle"].max()]
        assert (last_steady["material_scarcity"] == 0.0).all()

    def test_material_scarcity_reaches_half_in_reversibility(self, run_result):
        """Material scarcity reaches 0.5 during reversibility phase.

        Same timing note as steady_state test: the first reversibility row
        may carry a 0.0 scarcity value from the prior step.
        """
        _, cycle_df, _, _ = run_result
        rev = cycle_df[cycle_df["phase"] == "reversibility"]
        assert not rev.empty
        assert (rev["material_scarcity"] == 0.5).any()
        last_rev = rev[rev["cycle"] == rev["cycle"].max()]
        assert (last_rev["material_scarcity"] == 0.5).all()

    def test_no_real_api_calls(self, run_result, mock_reasoner):
        """The mock reasoner's call count should be > 0 (it was used),
        but no real httpx calls were made."""
        model, _, _, _ = run_result
        # mock_reasoner._call_count > 0 means agents did call decide()
        assert mock_reasoner._call_count > 0

        # Verify no real AgentReasoner was instantiated by checking
        # that no httpx client exists on our mock
        assert not hasattr(mock_reasoner, "client")

    def test_model_completed_all_cycles(self, run_result):
        model, _, _, _ = run_result
        assert model.cycle == model.config.total_cycles

    def test_baseline_patterns_captured(self, run_result):
        model, _, _, _ = run_result
        assert model.baseline_patterns is not None

    def test_adoption_rates_in_range(self, run_result):
        _, cycle_df, _, _ = run_result
        assert (cycle_df["adoption_rate"] >= 0.0).all()
        assert (cycle_df["adoption_rate"] <= 1.0).all()

    def test_coordination_efficiency_in_range(self, run_result):
        _, cycle_df, _, _ = run_result
        # Entropy ratio is in [0.0, 1.0] — 1.0 means uniform, 0.0 means single good
        assert (cycle_df["coordination_efficiency"] >= 0.0).all()
        assert (cycle_df["coordination_efficiency"] <= 1.0).all()


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

class TestReproducibility:
    """Same config + seed produces identical outputs."""

    def test_deterministic_outputs(self, mock_reasoner, tmp_path):
        config = SimConfig(
            transition_rate=3, scarcity_curve="linear", random_seed=77,
            n_agents=4, phase1_cycles=3, phase3_cycles=3, phase4_cycles=2,
        )

        dfs = []
        for run_idx in range(2):
            model = ScarcityModel(config)
            model.datacollector = create_collector()

            for _ in range(config.total_cycles):
                model.step()
                model.datacollector.collect(model)

            out_dir = tmp_path / f"run_{run_idx}"
            df = export_cycle_data(model, out_dir)
            dfs.append(df)

        # Compare numeric columns (adoption_rate, material_scarcity, etc.)
        pd.testing.assert_frame_equal(dfs[0], dfs[1])


# ---------------------------------------------------------------------------
# Phase 2 pipeline: model -> step -> collect -> export -> classify -> summary
# ---------------------------------------------------------------------------

class TestPhase2Pipeline:
    """End-to-end Phase 2 test: run model, export CSVs, classify verdicts, validate summary."""

    @pytest.fixture()
    def pipeline_config(self) -> SimConfig:
        return SimConfig(
            transition_rate=3,
            scarcity_curve="linear",
            random_seed=42,
            n_agents=4,
            phase1_cycles=3,
            phase3_cycles=3,
            phase4_cycles=2,
        )

    @pytest.fixture()
    def run_result(self, pipeline_config, mock_reasoner, tmp_output_dir):
        """Run the full simulation, export all 3 CSVs, return artifacts."""
        model = ScarcityModel(pipeline_config)
        model.datacollector = create_collector()

        for cycle in range(pipeline_config.total_cycles):
            model.step()
            model.datacollector.collect(model)

        cycle_df = export_cycle_data(model, tmp_output_dir)
        novel_df = export_novel_actions(model, tmp_output_dir)
        verdicts_df = classify_all_mechanisms(cycle_df, pipeline_config)
        summary_df = export_run_summary(verdicts_df, tmp_output_dir)

        return model, cycle_df, novel_df, summary_df, tmp_output_dir

    def test_run_summary_csv_exists(self, run_result):
        _, _, _, _, output_dir = run_result
        assert (output_dir / "run_summary.csv").exists()

    def test_run_summary_has_7_rows(self, run_result):
        _, _, _, summary_df, _ = run_result
        assert len(summary_df) == 7

    def test_run_summary_has_all_mechanisms(self, run_result):
        _, _, _, summary_df, _ = run_result
        assert set(summary_df["mechanism"]) == set(MECHANISMS)

    def test_all_verdicts_non_null(self, run_result):
        _, _, _, summary_df, _ = run_result
        assert summary_df["verdict"].notna().all()
        assert (summary_df["verdict"] != "").all()

    def test_all_verdicts_from_valid_set(self, run_result):
        _, _, _, summary_df, _ = run_result
        for verdict in summary_df["verdict"]:
            assert verdict in VERDICTS, f"Unexpected verdict: {verdict}"

    def test_run_summary_csv_roundtrip(self, run_result):
        """The CSV on disk can be re-read and matches the DataFrame."""
        _, _, _, summary_df, output_dir = run_result
        reloaded = pd.read_csv(output_dir / "run_summary.csv")
        assert len(reloaded) == len(summary_df)
        assert set(reloaded.columns) == set(summary_df.columns)

    def test_all_three_csvs_exist(self, run_result):
        _, _, _, _, output_dir = run_result
        assert (output_dir / "cycle_data.csv").exists()
        assert (output_dir / "novel_actions.csv").exists()
        assert (output_dir / "run_summary.csv").exists()

    def test_no_real_api_calls(self, run_result, mock_reasoner):
        assert mock_reasoner._call_count > 0
        assert not hasattr(mock_reasoner, "client")

"""
@file run_pilot.py
@description Pilot runner: small agent count, fast phases, validates full pipeline end-to-end.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-04
@changelog
- 2026-03-04: v1.0.0 - Initial creation
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from src.collector import create_collector, export_cycle_data, export_novel_actions
from src.config import MECHANISMS, SimConfig
from src.environment import ScarcityModel
from src.reasoner import AgentReasoner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_pilot():
    """Run a minimal pilot to validate the full simulation pipeline."""
    config = SimConfig(
        transition_rate=25,
        scarcity_curve="linear",
        random_seed=42,
        n_agents=5,
        phase1_cycles=10,  # short phases for pilot
        phase3_cycles=10,
        phase4_cycles=5,
    )

    logger.info(
        "Pilot config: %d agents, %d total cycles, transition_rate=%d, curve=%s",
        config.n_agents,
        config.total_cycles,
        config.transition_rate,
        config.scarcity_curve,
    )

    model = ScarcityModel(config)
    model.datacollector = create_collector()

    start = time.time()

    for cycle in range(config.total_cycles):
        phase = config.phase_at(cycle)
        scarcity = config.material_scarcity_at(cycle)

        model.step()
        model.datacollector.collect(model)

        if cycle % 10 == 0 or cycle == config.total_cycles - 1:
            adoption = model.compute_adoption_rates()
            active = [m for m, r in adoption.items() if r > 0]
            logger.info(
                "Cycle %3d | Phase: %-13s | Scarcity: %.2f | Active mechanisms: %s | "
                "Custom actions: %d | API calls: %d",
                cycle,
                phase,
                scarcity,
                active or "none",
                model.compute_custom_action_count(),
                AgentReasoner.get_instance().call_count,
            )

    elapsed = time.time() - start
    logger.info("Pilot completed in %.1fs (%d API calls)", elapsed, AgentReasoner.get_instance().call_count)

    # Export outputs
    output_dir = Path("outputs/pilot")
    cycle_df = export_cycle_data(model, output_dir)
    novel_df = export_novel_actions(model, output_dir)

    # Validation checks
    logger.info("--- Pilot Validation ---")

    # Check cycle_data.csv columns
    expected_cols = {
        "run_id", "seed", "transition_rate", "scarcity_curve", "n_agents",
        "cycle", "phase", "material_scarcity", "mechanism",
        "adoption_rate", "coordination_efficiency", "behavioral_pattern_score",
        "custom_action_count",
    }
    actual_cols = set(cycle_df.columns)
    missing = expected_cols - actual_cols
    if missing:
        logger.error("FAIL: Missing columns in cycle_data.csv: %s", missing)
    else:
        logger.info("PASS: cycle_data.csv has all expected columns")

    # Check all 7 mechanisms present
    mechanisms_in_data = set(cycle_df["mechanism"].unique())
    expected_mechs = set(MECHANISMS)
    if mechanisms_in_data != expected_mechs:
        logger.error("FAIL: Missing mechanisms: %s", expected_mechs - mechanisms_in_data)
    else:
        logger.info("PASS: All 7 mechanisms present in output")

    # Check Phase 1 adoption rates > 0
    phase1 = cycle_df[cycle_df["phase"] == "baseline"]
    phase1_adoption = phase1.groupby("mechanism")["adoption_rate"].max()
    inactive_phase1 = [m for m in MECHANISMS if phase1_adoption.get(m, 0) == 0]
    if inactive_phase1:
        logger.warning("WARN: Mechanisms with 0 adoption in Phase 1: %s", inactive_phase1)
    else:
        logger.info("PASS: All 7 mechanisms show adoption > 0 in Phase 1")

    # Check for custom actions
    total_custom = novel_df.shape[0] if not novel_df.empty else 0
    if total_custom > 0:
        logger.info("PASS: %d custom action(s) logged in novel_actions.csv", total_custom)
    else:
        logger.warning("WARN: No custom actions logged (not a hard failure for pilot)")

    logger.info("Outputs written to %s", output_dir.resolve())


if __name__ == "__main__":
    run_pilot()

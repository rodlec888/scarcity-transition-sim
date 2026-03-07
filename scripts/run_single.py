"""
@file run_single.py
@description Full 5-phase runner with verdict classification and retroanalysis.
    Accepts CLI args for transition rate, scarcity curve, and seed.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-06
@changelog
- 2026-03-06: v1.0.0 - Initial creation
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from src.collector import (
    create_collector,
    export_agent_actions,
    export_cycle_data,
    export_novel_actions,
    export_run_summary,
)
from src.config import MECHANISMS, SimConfig
from src.environment import ScarcityModel
from src.reasoner import AgentReasoner
from src.retroanalysis import trace_replacement_chains
from src.verdicts import classify_all_mechanisms

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a full scarcity-transition simulation with all 5 phases.",
    )
    parser.add_argument(
        "--transition-rate",
        type=int,
        default=25,
        help="Phase 2 duration in cycles (default: 25).",
    )
    parser.add_argument(
        "--curve",
        type=str,
        default="linear",
        choices=["linear", "exponential", "step"],
        help="Scarcity decay curve shape (default: linear).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--n-agents",
        type=int,
        default=100,
        help="Number of agents (default: 100).",
    )
    parser.add_argument(
        "--phase1-cycles",
        type=int,
        default=200,
        help="Phase 1 (baseline) duration in cycles (default: 200).",
    )
    parser.add_argument(
        "--phase3-cycles",
        type=int,
        default=200,
        help="Phase 3 (steady-state) duration in cycles (default: 200).",
    )
    parser.add_argument(
        "--phase4-cycles",
        type=int,
        default=50,
        help="Phase 4 (reversibility) duration in cycles (default: 50).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory. Defaults to outputs/<run_id>/.",
    )
    return parser.parse_args()


def _collect_raw_actions_by_mechanism(
    model: ScarcityModel,
) -> dict[str, dict[str, list[dict]]]:
    """Build mechanism -> phase -> list[action] mapping from agent histories.

    Used for goods_domain Jaccard computation in verdict classification.
    """
    result: dict[str, dict[str, list[dict]]] = {
        m: {"baseline": [], "transition": [], "steady_state": [], "reversibility": []}
        for m in MECHANISMS
    }
    result["custom"] = {
        "baseline": [], "transition": [], "steady_state": [], "reversibility": [],
    }

    for agent in model.agents_list:
        for action in agent.action_history:
            mech = action.get("mechanism", "custom")
            cycle = action.get("cycle", 0)
            phase = model.config.phase_at(cycle)

            if mech in result:
                result[mech][phase].append(action)

    return result


def _write_run_metadata(
    output_dir: Path,
    run_id: str,
    config: SimConfig,
    start_utc: str,
    elapsed_s: float,
    api_calls: int,
    verdicts: dict[str, str],
    notes: str = "",
) -> None:
    """Write run_metadata.json with all parameters and context for result interpretation."""
    import mesa

    metadata = {
        "run_id": run_id,
        "started_at_utc": start_utc,
        "elapsed_seconds": round(elapsed_s, 1),
        "api_calls": api_calls,
        "config": {k: v for k, v in asdict(config).items()},
        "environment": {
            "xai_model": os.getenv("XAI_MODEL", "unknown"),
            "mesa_version": mesa.__version__,
        },
        "verdicts": verdicts,
        "notes": notes,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, default=str) + "\n"
    )


def run_single(args: argparse.Namespace) -> None:
    """Run a full simulation, classify verdicts, and export all outputs."""
    config = SimConfig(
        transition_rate=args.transition_rate,
        scarcity_curve=args.curve,
        random_seed=args.seed,
        n_agents=args.n_agents,
        phase1_cycles=args.phase1_cycles,
        phase3_cycles=args.phase3_cycles,
        phase4_cycles=args.phase4_cycles,
    )

    start_utc = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"run_{config.random_seed}_{config.transition_rate}_{config.scarcity_curve}_{ts}"
    output_dir = Path(args.output_dir) if args.output_dir else Path("outputs") / run_id

    logger.info(
        "Config: %d agents, %d total cycles, transition_rate=%d, curve=%s, seed=%d",
        config.n_agents,
        config.total_cycles,
        config.transition_rate,
        config.scarcity_curve,
        config.random_seed,
    )
    logger.info("Output dir: %s", output_dir.resolve())

    # --- Phase 1-4: Run simulation ---
    model = ScarcityModel(config)
    model.datacollector = create_collector()

    start = time.time()

    for cycle in range(config.total_cycles):
        phase = config.phase_at(cycle)
        model.step()
        model.datacollector.collect(model)

        # Log progress every 50 cycles
        if cycle % 50 == 0 or cycle == config.total_cycles - 1:
            adoption = model.compute_adoption_rates()
            active = [m for m, r in adoption.items() if r > 0]
            logger.info(
                "Cycle %4d / %d | Phase: %-13s | Scarcity: %.2f | Active: %s | "
                "API calls: %d",
                cycle,
                config.total_cycles,
                phase,
                config.material_scarcity_at(cycle),
                active or "none",
                AgentReasoner.get_instance().call_count,
            )

    sim_elapsed = time.time() - start
    logger.info(
        "Simulation completed in %.1fs (%d API calls)",
        sim_elapsed,
        AgentReasoner.get_instance().call_count,
    )

    # --- Export all CSVs ---
    cycle_df = export_cycle_data(model, output_dir)
    novel_df = export_novel_actions(model, output_dir)
    actions_df = export_agent_actions(model, output_dir)
    logger.info(
        "Exported cycle_data.csv (%d rows), novel_actions.csv (%d rows), "
        "agent_actions.csv (%d rows)",
        len(cycle_df),
        len(novel_df),
        len(actions_df),
    )

    # --- Phase 5: Retroanalysis ---
    logger.info("--- Running verdict classification ---")

    # Collect raw actions for Jaccard computation
    raw_actions = _collect_raw_actions_by_mechanism(model)

    # Classify all mechanisms
    verdicts_df = classify_all_mechanisms(cycle_df, config, raw_actions)
    export_run_summary(verdicts_df, output_dir)

    for _, row in verdicts_df.iterrows():
        logger.info(
            "  %-12s -> %-18s (adoption=%.3f, efficiency=%.3f, BPS=%.3f, Jaccard=%.3f)",
            row["mechanism"],
            row["verdict"],
            row["mean_adoption_phase3"],
            row["mean_efficiency_phase3"],
            row["behavioral_pattern_score"],
            row["goods_domain_jaccard"],
        )

    # Trace replacement chains for collapsed mechanisms
    chains = trace_replacement_chains(cycle_df, config)
    if chains:
        logger.info("--- Replacement chains ---")
        for chain in chains:
            replacements = chain["replacement_mechanisms"]
            rep_str = ", ".join(
                f"{r['mechanism']} (+{r['adoption_increase']:.3f})"
                for r in replacements[:3]
            ) or "none identified"
            logger.info(
                "  %s collapsed (cycles %d-%d) -> replaced by: %s",
                chain["collapsed_mechanism"],
                chain["collapse_start_cycle"],
                chain["collapse_end_cycle"],
                rep_str,
            )
    else:
        logger.info("No mechanisms collapsed — no replacement chains to trace.")

    # --- Write run metadata ---
    verdict_map = {row["mechanism"]: row["verdict"] for _, row in verdicts_df.iterrows()}
    _write_run_metadata(
        output_dir=output_dir,
        run_id=run_id,
        config=config,
        start_utc=start_utc,
        elapsed_s=sim_elapsed,
        api_calls=AgentReasoner.get_instance().call_count,
        verdicts=verdict_map,
    )

    logger.info("All outputs written to %s", output_dir.resolve())


if __name__ == "__main__":
    run_single(parse_args())

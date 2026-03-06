"""
@file retroanalysis.py
@description Post-processing: replacement chain tracing and information structure checks.
    Pure data processing (pandas + math), no Mesa or httpx dependencies.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-06
@changelog
- 2026-03-06: v1.0.0 - Initial creation
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from src.config import MECHANISMS, SimConfig

logger = logging.getLogger(__name__)


def trace_replacement_chains(
    cycle_df: pd.DataFrame,
    config: SimConfig,
) -> list[dict[str, Any]]:
    """For each collapsed mechanism, identify what replaced it.

    Looks for mechanisms whose adoption increased during the same cycle
    window where the collapsed mechanism fell below threshold.

    Args:
        cycle_df: Full cycle_data DataFrame for one run.
        config: Simulation configuration with thresholds.

    Returns:
        List of dicts, one per collapsed mechanism, with replacement info:
        {
            collapsed_mechanism, collapse_start_cycle, collapse_end_cycle,
            replacement_mechanisms: [{mechanism, adoption_increase, cycle_range}],
        }
    """
    results: list[dict[str, Any]] = []

    phase3 = cycle_df[cycle_df["phase"] == "steady_state"].copy()
    if phase3.empty:
        return results

    for mechanism in MECHANISMS:
        mech_data = phase3[phase3["mechanism"] == mechanism].sort_values("cycle")
        if mech_data.empty:
            continue

        # Find the first run of collapse_sustained_n consecutive cycles below threshold
        collapse_start: int | None = None
        collapse_end: int | None = None
        run_start: int | None = None
        count = 0

        for _, row in mech_data.iterrows():
            cycle = int(row["cycle"])
            adoption = float(row["adoption_rate"])

            if adoption < config.collapse_threshold:
                if count == 0:
                    run_start = cycle
                count += 1
                if count >= config.collapse_sustained_n:
                    collapse_start = run_start
                    collapse_end = cycle
                    break
            else:
                count = 0
                run_start = None

        if collapse_start is None or collapse_end is None:
            continue

        # Find which mechanisms gained adoption during the collapse window
        window = phase3[
            (phase3["cycle"] >= collapse_start) & (phase3["cycle"] <= collapse_end)
        ]
        replacements: list[dict[str, Any]] = []

        for other_mech in MECHANISMS:
            if other_mech == mechanism:
                continue

            other_window = window[window["mechanism"] == other_mech].sort_values("cycle")
            if other_window.empty:
                continue

            # Compare first and last adoption in the window
            first_adoption = float(other_window.iloc[0]["adoption_rate"])
            last_adoption = float(other_window.iloc[-1]["adoption_rate"])
            increase = last_adoption - first_adoption

            if increase > 0.0:
                replacements.append({
                    "mechanism": other_mech,
                    "adoption_increase": round(increase, 4),
                    "cycle_range": (int(other_window.iloc[0]["cycle"]),
                                    int(other_window.iloc[-1]["cycle"])),
                })

        # Sort by adoption increase descending
        replacements.sort(key=lambda r: r["adoption_increase"], reverse=True)

        results.append({
            "collapsed_mechanism": mechanism,
            "collapse_start_cycle": collapse_start,
            "collapse_end_cycle": collapse_end,
            "replacement_mechanisms": replacements,
        })

    return results


def information_structure_check(
    mechanism: str,
    phase1_actions: list[dict[str, Any]],
    phase3_actions: list[dict[str, Any]],
) -> str:
    """Determine if a repurposed mechanism represents discovery or labeling.

    Discovery: the mechanism's Phase 3 actions involve goods that existed in
    Phase 1 but were not targeted by this mechanism in Phase 1. The mechanism
    found a new application for existing goods.

    Labeling: >30% of Phase 3 target_good values are entirely absent from
    the Phase 1 goods vocabulary (all mechanisms combined). The mechanism
    created or recognized new categories.

    Args:
        mechanism: The mechanism being checked (for logging context).
        phase1_actions: All actions (across all mechanisms) from Phase 1.
        phase3_actions: Actions for this specific mechanism in Phase 3.

    Returns:
        "discovery" or "labeling".
    """
    # All goods that appeared anywhere in Phase 1
    phase1_all_goods = {
        a.get("target_good") for a in phase1_actions if a.get("target_good")
    }

    # Goods targeted by this mechanism in Phase 3
    phase3_mech_goods = [
        a.get("target_good") for a in phase3_actions if a.get("target_good")
    ]

    if not phase3_mech_goods:
        logger.debug(
            "No target_good values for mechanism '%s' in Phase 3 — defaulting to discovery.",
            mechanism,
        )
        return "discovery"

    # Count how many Phase 3 goods are completely novel (absent from all Phase 1 actions)
    novel_count = sum(1 for g in phase3_mech_goods if g not in phase1_all_goods)
    novel_ratio = novel_count / len(phase3_mech_goods)

    if novel_ratio > 0.3:
        return "labeling"
    return "discovery"

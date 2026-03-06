"""
@file verdicts.py
@description Verdict classification engine — decision tree from ADR-002.
    Pure data processing: takes cycle_data DataFrame, returns per-mechanism verdicts.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-06
@changelog
- 2026-03-06: v1.0.0 - Initial creation implementing full ADR-002 decision tree
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from src.config import MECHANISMS, SimConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _check_consecutive_below(series: pd.Series, threshold: float, n: int) -> bool:
    """Check if there are n consecutive values strictly below threshold.

    Args:
        series: Ordered numeric series (e.g., adoption_rate by cycle).
        threshold: Upper bound (exclusive).
        n: Required consecutive count.

    Returns:
        True if any run of n+ consecutive values < threshold exists.
    """
    if len(series) < n:
        return False

    count = 0
    for val in series:
        if val < threshold:
            count += 1
            if count >= n:
                return True
        else:
            count = 0
    return False


def _check_consecutive_above(series: pd.Series, threshold: float, n: int) -> bool:
    """Check if there are n consecutive values at or above threshold.

    Args:
        series: Ordered numeric series.
        threshold: Lower bound (inclusive).
        n: Required consecutive count.

    Returns:
        True if any run of n+ consecutive values >= threshold exists.
    """
    if len(series) < n:
        return False

    count = 0
    for val in series:
        if val >= threshold:
            count += 1
            if count >= n:
                return True
        else:
            count = 0
    return False


def _compute_goods_domain_jaccard(
    phase1_actions: list[dict[str, Any]],
    phase3_actions: list[dict[str, Any]],
) -> float:
    """Jaccard similarity of target_good sets between two action lists.

    Args:
        phase1_actions: Actions from Phase 1 (baseline).
        phase3_actions: Actions from Phase 3 (steady-state).

    Returns:
        Jaccard index in [0.0, 1.0]. Returns 1.0 if both sets are empty.
    """
    goods_1 = {a.get("target_good") for a in phase1_actions if a.get("target_good")}
    goods_3 = {a.get("target_good") for a in phase3_actions if a.get("target_good")}

    if not goods_1 and not goods_3:
        return 1.0
    if not goods_1 or not goods_3:
        return 0.0

    intersection = goods_1 & goods_3
    union = goods_1 | goods_3
    return len(intersection) / len(union)


def _extract_mechanism_actions(
    cycle_df: pd.DataFrame,
    mechanism: str,
    phase: str,
) -> list[dict[str, Any]]:
    """Extract raw action dicts for a mechanism in a given phase.

    This reconstructs minimal action dicts from cycle_data columns.
    For goods_domain comparison, we only need target_good which is not
    in cycle_data. Returns empty list — callers needing raw actions
    should use model.cycle_actions or agent.action_history directly.

    For the DataFrame-based verdict pipeline, we work with aggregated
    metrics (adoption_rate, coordination_efficiency, behavioral_pattern_score)
    rather than raw actions.
    """
    mask = (cycle_df["mechanism"] == mechanism) & (cycle_df["phase"] == phase)
    return cycle_df[mask].to_dict("records")


# ---------------------------------------------------------------------------
# Single mechanism classification
# ---------------------------------------------------------------------------


def classify_mechanism(
    mechanism: str,
    phase3_data: pd.DataFrame,
    phase4_data: pd.DataFrame,
    phase1_data: pd.DataFrame,
    config: SimConfig,
) -> dict[str, Any]:
    """Classify a single mechanism's fate using the ADR-002 decision tree.

    Args:
        mechanism: One of the 7 coordination mechanisms.
        phase3_data: Rows for this mechanism in the steady_state phase,
            sorted by cycle.
        phase4_data: Rows for this mechanism in the reversibility phase,
            sorted by cycle.
        phase1_data: Rows for this mechanism in the baseline phase,
            sorted by cycle.
        config: Simulation configuration with all thresholds.

    Returns:
        Dict with verdict and supporting metrics.
    """
    result: dict[str, Any] = {
        "mechanism": mechanism,
        "verdict": "PERSIST_IDLE",  # default
        "collapse_triggered": False,
        "recovery_triggered": False,
        "mean_adoption_phase3": 0.0,
        "mean_efficiency_phase3": 1.0,
        "behavioral_pattern_score": 0.0,
        "goods_domain_jaccard": 1.0,
        "notes": "",
    }

    # Compute summary metrics
    if not phase3_data.empty:
        result["mean_adoption_phase3"] = float(phase3_data["adoption_rate"].mean())
        result["mean_efficiency_phase3"] = float(phase3_data["coordination_efficiency"].mean())

    # Mean BPS over Phase 3
    if not phase3_data.empty:
        result["behavioral_pattern_score"] = float(
            phase3_data["behavioral_pattern_score"].mean()
        )

    # --- Step 1: Collapse check ---
    if not phase3_data.empty:
        adoption_series = phase3_data.sort_values("cycle")["adoption_rate"]
        collapse = _check_consecutive_below(
            adoption_series,
            config.collapse_threshold,
            config.collapse_sustained_n,
        )
    else:
        collapse = False

    if collapse:
        result["collapse_triggered"] = True

        # Check Phase 4 recovery
        if not phase4_data.empty:
            recovery_series = phase4_data.sort_values("cycle")["adoption_rate"]
            recovery = _check_consecutive_above(
                recovery_series,
                config.recovery_adoption_threshold,
                config.recovery_sustained_n,
            )
        else:
            recovery = False

        if recovery:
            result["recovery_triggered"] = True
            result["verdict"] = "PERSIST_DORMANT"
            result["notes"] = "Collapsed in Phase 3 but recovered in Phase 4."
        else:
            result["verdict"] = "COLLAPSE"
            result["notes"] = "Sustained below collapse threshold with no recovery."
        return result

    # --- Step 2: Idle check ---
    mean_eff = result["mean_efficiency_phase3"]
    lo, hi = config.efficiency_idle_band

    if lo <= mean_eff <= hi:
        result["verdict"] = "PERSIST_IDLE"
        result["notes"] = (
            f"Efficiency {mean_eff:.3f} within idle band [{lo}, {hi}]."
        )
        return result

    # --- Step 3: Active / Repurpose / Novel ---
    bps = result["behavioral_pattern_score"]
    threshold = config.behavioral_pattern_threshold

    if bps < threshold:
        result["verdict"] = "NOVEL_MECHANISM"
        result["notes"] = (
            f"BPS {bps:.3f} < {threshold} — action distribution diverged from baseline."
        )
        return result

    # BPS >= threshold — check goods domain
    # Compute Jaccard from the cycle_data rows (using target_good if available,
    # otherwise fall back to a placeholder).
    # Since cycle_data does not carry per-action target_good, we use the
    # goods_domain_jaccard passed in or default to 1.0 (same domain).
    # In the full pipeline, this is computed from raw action histories.
    jaccard = result["goods_domain_jaccard"]

    if jaccard >= config.goods_domain_jaccard_threshold:
        result["verdict"] = "PERSIST_ACTIVE"
        result["notes"] = (
            f"BPS {bps:.3f} >= {threshold}, Jaccard {jaccard:.3f} >= "
            f"{config.goods_domain_jaccard_threshold} — same role, enhanced efficiency."
        )
    else:
        # Different goods domain — default to REPURPOSE (conservative per ADR-002)
        result["verdict"] = "REPURPOSE"
        result["notes"] = (
            f"BPS {bps:.3f} >= {threshold}, Jaccard {jaccard:.3f} < "
            f"{config.goods_domain_jaccard_threshold} — mechanism applied to new goods domain."
        )

    return result


# ---------------------------------------------------------------------------
# Classify all mechanisms
# ---------------------------------------------------------------------------


def classify_all_mechanisms(
    cycle_df: pd.DataFrame,
    config: SimConfig,
    raw_actions: dict[str, dict[str, list[dict[str, Any]]]] | None = None,
) -> pd.DataFrame:
    """Classify all 7 mechanisms and return a run_summary DataFrame.

    Args:
        cycle_df: Full cycle_data DataFrame for one run.
        config: Simulation configuration.
        raw_actions: Optional dict mapping mechanism -> phase -> list of raw
            action dicts (for Jaccard computation). If None, Jaccard defaults
            to 1.0 (same domain assumed).

    Returns:
        DataFrame with one row per mechanism, matching run_summary.csv schema.
    """
    rows: list[dict[str, Any]] = []

    for mechanism in MECHANISMS:
        phase1 = cycle_df[
            (cycle_df["mechanism"] == mechanism) & (cycle_df["phase"] == "baseline")
        ].sort_values("cycle")

        phase3 = cycle_df[
            (cycle_df["mechanism"] == mechanism) & (cycle_df["phase"] == "steady_state")
        ].sort_values("cycle")

        phase4 = cycle_df[
            (cycle_df["mechanism"] == mechanism) & (cycle_df["phase"] == "reversibility")
        ].sort_values("cycle")

        result = classify_mechanism(mechanism, phase3, phase4, phase1, config)

        # Compute Jaccard from raw actions if available
        if raw_actions and mechanism in raw_actions:
            mech_actions = raw_actions[mechanism]
            p1_actions = mech_actions.get("baseline", [])
            p3_actions = mech_actions.get("steady_state", [])
            jaccard = _compute_goods_domain_jaccard(p1_actions, p3_actions)
            result["goods_domain_jaccard"] = jaccard

            # Re-evaluate verdict if Jaccard changes the outcome
            # (only matters if we passed the idle check and BPS >= threshold)
            if (
                not result["collapse_triggered"]
                and result["mean_efficiency_phase3"] > config.efficiency_idle_band[1]
                and result["behavioral_pattern_score"] >= config.behavioral_pattern_threshold
            ):
                if jaccard >= config.goods_domain_jaccard_threshold:
                    result["verdict"] = "PERSIST_ACTIVE"
                    result["notes"] = (
                        f"BPS {result['behavioral_pattern_score']:.3f} >= "
                        f"{config.behavioral_pattern_threshold}, "
                        f"Jaccard {jaccard:.3f} >= "
                        f"{config.goods_domain_jaccard_threshold} — same role."
                    )
                else:
                    result["verdict"] = "REPURPOSE"
                    result["notes"] = (
                        f"BPS {result['behavioral_pattern_score']:.3f} >= "
                        f"{config.behavioral_pattern_threshold}, "
                        f"Jaccard {jaccard:.3f} < "
                        f"{config.goods_domain_jaccard_threshold} — new goods domain."
                    )

        # Add run-level metadata
        result["run_id"] = config.random_seed
        result["seed"] = config.random_seed
        result["transition_rate"] = config.transition_rate
        result["scarcity_curve"] = config.scarcity_curve
        result["n_agents"] = config.n_agents

        rows.append(result)

    # Build DataFrame with consistent column order
    columns = [
        "run_id", "seed", "transition_rate", "scarcity_curve", "n_agents",
        "mechanism", "verdict",
        "collapse_triggered", "recovery_triggered",
        "mean_adoption_phase3", "mean_efficiency_phase3",
        "behavioral_pattern_score", "goods_domain_jaccard",
        "notes",
    ]
    return pd.DataFrame(rows, columns=columns)

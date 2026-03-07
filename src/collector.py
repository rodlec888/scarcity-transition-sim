"""
@file collector.py
@description Mesa DataCollector wired to cycle_data.csv schema.
@author ScarcityTransitionSim_Dev
@version 1.1.0
@date 2026-03-04
@changelog
- 2026-03-06: v1.1.0 - Real coordination_efficiency (entropy ratio) + run_summary export
- 2026-03-04: v1.0.0 - Initial creation
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from mesa import DataCollector

from src.config import MECHANISMS

if TYPE_CHECKING:
    from src.environment import ScarcityModel


def _compute_coordination_efficiency(actions: list[dict], n_goods: int) -> float:
    """Entropy ratio of target_good distribution vs uniform distribution.

    Measures how much a mechanism concentrates coordination on specific goods
    compared to a random (uniform) allocation. Ratio ~1.0 means idle (uniform),
    <1.0 means concentrated, >1.0 is not possible with Shannon entropy ratio
    but the metric is clamped to observed behavior.

    Args:
        actions: List of action dicts for one mechanism in one cycle.
        n_goods: Total number of distinct goods in the simulation.

    Returns:
        Entropy ratio in [0.0, 1.0]. Returns 1.0 if no actions or single good.
    """
    if not actions or n_goods <= 1:
        return 1.0

    counts: dict[str, int] = {}
    for a in actions:
        good = a.get("target_good")
        if good:
            counts[good] = counts.get(good, 0) + 1

    if not counts:
        return 1.0

    total = sum(counts.values())
    actual_entropy = -sum(
        (c / total) * math.log2(c / total) for c in counts.values() if c > 0
    )
    max_entropy = math.log2(n_goods)

    if max_entropy == 0:
        return 1.0
    ratio = actual_entropy / max_entropy
    # Normalize -0.0 to 0.0 for clean output
    return ratio + 0.0


def _cosine_similarity(a: dict[str, int], b: dict[str, int]) -> float:
    """Cosine similarity between two sparse count vectors (dicts).

    Args:
        a: First vector as {key: count}.
        b: Second vector as {key: count}.

    Returns:
        Similarity in [0.0, 1.0]. Returns 0.0 if either vector is empty.
    """
    if not a or not b:
        return 0.0

    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    mag_a = math.sqrt(sum(v**2 for v in a.values()))
    mag_b = math.sqrt(sum(v**2 for v in b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def create_collector() -> DataCollector:
    """Create a Mesa DataCollector that captures per-mechanism metrics each cycle.

    The collector uses model-level reporters that return one dict per mechanism.
    These are expanded into the flat cycle_data.csv schema at export time.
    """
    return DataCollector(
        model_reporters={
            "cycle_metrics": _collect_cycle_metrics,
        }
    )


def _collect_cycle_metrics(model: ScarcityModel) -> list[dict]:
    """Collect per-mechanism metrics for the current cycle.

    Returns:
        List of dicts, one per mechanism, matching cycle_data.csv columns.
    """
    adoption_rates = model.compute_adoption_rates()
    current_patterns = model._compute_behavioral_patterns()
    custom_count = model.compute_custom_action_count()

    # Total number of distinct goods for entropy normalization
    from src.environment import MATERIAL_GOODS, INHERENT_GOODS

    n_goods = len(MATERIAL_GOODS) + len(INHERENT_GOODS)

    # Group current cycle actions by mechanism for efficiency computation
    actions_by_mechanism: dict[str, list[dict]] = {m: [] for m in MECHANISMS}
    for action in model.cycle_actions:
        mech = action.get("mechanism")
        if mech in actions_by_mechanism:
            actions_by_mechanism[mech].append(action)

    rows = []
    for mechanism in MECHANISMS:
        # Behavioral pattern score: cosine sim to Phase 1 baseline
        bps = 0.0
        if model.baseline_patterns and mechanism in model.baseline_patterns:
            bps = _cosine_similarity(
                current_patterns.get(mechanism, {}),
                model.baseline_patterns[mechanism],
            )

        # Coordination efficiency: entropy ratio
        eff = _compute_coordination_efficiency(
            actions_by_mechanism[mechanism], n_goods
        )

        rows.append(
            {
                "run_id": model.config.random_seed,  # unique per seed for now
                "seed": model.config.random_seed,
                "transition_rate": model.config.transition_rate,
                "scarcity_curve": model.config.scarcity_curve,
                "n_agents": model.config.n_agents,
                "cycle": model.cycle,
                "phase": model.phase,
                "material_scarcity": model.material_scarcity,
                "mechanism": mechanism,
                "adoption_rate": adoption_rates.get(mechanism, 0.0),
                "coordination_efficiency": eff,
                "behavioral_pattern_score": bps,
                "custom_action_count": custom_count if mechanism == MECHANISMS[0] else 0,
            }
        )
    return rows


def export_cycle_data(model: ScarcityModel, output_dir: Path):
    """Export collected data to cycle_data.csv.

    Args:
        model: The model with a DataCollector attached.
        output_dir: Directory to write the CSV into.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = model.datacollector.get_model_vars_dataframe()
    # raw["cycle_metrics"] is a Series of lists-of-dicts
    all_rows = []
    for _, row_list in raw["cycle_metrics"].items():
        if isinstance(row_list, list):
            all_rows.extend(row_list)

    df = pd.DataFrame(all_rows)
    df.to_csv(output_dir / "cycle_data.csv", index=False)
    return df


def export_novel_actions(model: ScarcityModel, output_dir: Path):
    """Export custom actions log to novel_actions.csv.

    Args:
        model: The model instance.
        output_dir: Directory to write the CSV into.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gather all custom actions from all agents
    rows = []
    for agent in model.agents_list:
        for action in agent.action_history:
            if action.get("mechanism") == "custom":
                persona = agent.persona
                rows.append(
                    {
                        "run_id": model.config.random_seed,
                        "cycle": action.get("cycle"),
                        "agent_id": agent.unique_id,
                        "persona_work_identity": persona.work_identity if persona else None,
                        "persona_adaptability": persona.adaptability if persona else None,
                        "free_text_description": action.get("reasoning", ""),
                        "classified_as": None,
                    }
                )

    df = pd.DataFrame(rows)
    df.to_csv(output_dir / "novel_actions.csv", index=False)
    return df


def export_agent_actions(model: ScarcityModel, output_dir: Path):
    """Export every individual agent decision to agent_actions.csv.

    Args:
        model: The model instance.
        output_dir: Directory to write the CSV into.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for agent in model.agents_list:
        persona = agent.persona
        for action in agent.action_history:
            rows.append(
                {
                    "run_id": model.config.random_seed,
                    "cycle": action.get("cycle"),
                    "agent_id": action.get("agent_id"),
                    "node_id": action.get("node_id"),
                    "mechanism": action.get("mechanism"),
                    "action_type": action.get("action_type"),
                    "target_good": action.get("target_good"),
                    "counterparty": action.get("counterparty"),
                    "reasoning": action.get("reasoning", ""),
                    "persona_work_identity": persona.work_identity if persona else None,
                    "persona_adaptability": persona.adaptability if persona else None,
                    "persona_social_orientation": persona.social_orientation if persona else None,
                    "persona_risk_tolerance": persona.risk_tolerance if persona else None,
                    "persona_resource_level": persona.resource_level if persona else None,
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(output_dir / "agent_actions.csv", index=False)
    return df


def export_run_summary(verdicts_df: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    """Export verdict classification to run_summary.csv.

    Args:
        verdicts_df: DataFrame from classify_all_mechanisms().
        output_dir: Directory to write the CSV into.

    Returns:
        The same DataFrame (pass-through for chaining).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    verdicts_df.to_csv(output_dir / "run_summary.csv", index=False)
    return verdicts_df

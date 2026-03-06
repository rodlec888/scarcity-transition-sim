"""
@file config.py
@description Central simulation configuration — all parameters in a single dataclass.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-04
@changelog
- 2026-03-04: v1.0.0 - Initial creation with all 11 parameters from architecture spec
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal


MECHANISMS = (
    "price",
    "money",
    "property",
    "employment",
    "taxation",
    "reputation",
    "queuing",
)

SCARCITY_CURVES = ("linear", "exponential", "step")

VERDICTS = (
    "COLLAPSE",
    "PERSIST_DORMANT",
    "PERSIST_IDLE",
    "PERSIST_ACTIVE",
    "REPURPOSE",
    "NOVEL_MECHANISM",
)


@dataclass(frozen=True)
class SimConfig:
    """Immutable configuration for a single simulation run.

    All 11 parameters from the formal parameter table in architecture.md.
    """

    # --- Sweep parameters (vary across runs) ---
    transition_rate: int = 25
    scarcity_curve: Literal["linear", "exponential", "step"] = "linear"
    random_seed: int = 42

    # --- Population ---
    n_agents: int = 100

    # --- Phase durations ---
    phase1_cycles: int = 200
    phase3_cycles: int = 200
    phase4_cycles: int = 50

    # --- Network ---
    network_topology: Literal["small_world"] = "small_world"
    interaction_budget: int = 3

    # --- Verdict thresholds ---
    collapse_threshold: float = 0.05
    collapse_sustained_n: int = 20

    # --- Derived (not stored, computed) ---

    @property
    def phase2_cycles(self) -> int:
        """Phase 2 duration equals the transition rate."""
        return self.transition_rate

    @property
    def total_cycles(self) -> int:
        return self.phase1_cycles + self.phase2_cycles + self.phase3_cycles + self.phase4_cycles

    def phase_at(self, cycle: int) -> str:
        """Return the phase name for a given cycle number (0-indexed)."""
        if cycle < self.phase1_cycles:
            return "baseline"
        if cycle < self.phase1_cycles + self.phase2_cycles:
            return "transition"
        if cycle < self.phase1_cycles + self.phase2_cycles + self.phase3_cycles:
            return "steady_state"
        return "reversibility"

    def material_scarcity_at(self, cycle: int) -> float:
        """Material goods scarcity level at a given cycle. Returns 0.0-1.0."""
        phase = self.phase_at(cycle)

        if phase == "baseline":
            return 1.0

        if phase == "transition":
            t = cycle - self.phase1_cycles
            return scarcity_at(t, self.transition_rate, self.scarcity_curve)

        if phase == "steady_state":
            return 0.0

        # reversibility — re-inject partial scarcity
        return 0.5


def scarcity_at(t: int, transition_rate: int, curve: str) -> float:
    """Material goods scarcity level at cycle t of Phase 2.

    Args:
        t: Cycle number within Phase 2 (0-indexed).
        transition_rate: Total Phase 2 duration in cycles.
        curve: Shape of scarcity decay — "linear", "exponential", or "step".

    Returns:
        Scarcity level between 0.0 and 1.0.
    """
    progress = t / transition_rate
    if curve == "linear":
        return max(0.0, 1.0 - progress)
    elif curve == "exponential":
        return math.exp(-5 * progress)
    elif curve == "step":
        return 0.0 if progress >= 1.0 else 1.0
    else:
        raise ValueError(f"Unknown scarcity curve: {curve}")

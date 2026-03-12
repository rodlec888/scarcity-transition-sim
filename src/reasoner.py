"""
@file reasoner.py
@description AgentReasoner: xAI API call, prompt construction, structured action response parsing.
    This is the ONLY class that touches the xAI API.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-04
@changelog
- 2026-03-04: v1.0.0 - Initial creation
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from typing import TYPE_CHECKING, Any

import httpx
from dotenv import load_dotenv

from src.agent import ACTION_VOCABULARY
from src.config import MECHANISMS

if TYPE_CHECKING:
    from src.agent import CoordinationAgent

load_dotenv()
logger = logging.getLogger(__name__)

# Singleton instance
_reasoner_instance: AgentReasoner | None = None


SYSTEM_PROMPT = """\
You are an economic agent in a multi-agent simulation studying coordination mechanisms \
under varying scarcity conditions.

Your task: Given your persona, the current environment state, and your recent history, \
choose ONE coordination action to take this cycle. You must respond with a JSON object \
containing exactly these fields:

{
  "mechanism": "<one of: price, money, property, employment, taxation, reputation, queuing, custom>",
  "action_type": "<a valid subtype for the chosen mechanism>",
  "target_good": "<what good or resource this action concerns>",
  "counterparty": "<neighbor agent ID you're interacting with, or null>",
  "reasoning": "<1-2 sentences explaining your choice>",
  "details": {}
}

Valid action subtypes per mechanism:
- price: bid, ask, accept_price
- money: pay, receive, save, lend
- property: claim, contest, enforce, transfer
- employment: offer_work, accept_work, compensate
- taxation: contribute, collect, distribute
- reputation: rate, endorse, check_reputation
- queuing: join_queue, advance, serve_next
- custom: custom (use this for novel coordination strategies not covered above)

Rules:
1. You MUST choose a mechanism and action_type from the vocabulary above.
2. If no standard mechanism fits your coordination need, use "custom" and describe \
your novel approach in the reasoning field.
3. Consider the current scarcity level. Some goods may become abundant while others \
remain scarce — you can redirect coordination mechanisms to where they are still needed.
4. Consider your persona traits when deciding strategy.
5. Respond ONLY with the JSON object. No other text.\
"""


def _build_behavioral_summary(agent: CoordinationAgent, window: int = 20) -> list[str]:
    """Build a self-reflection summary from the agent's action history.

    Returns prompt lines describing mechanism usage patterns, abandoned mechanisms,
    and scarcity trajectory — giving the agent continuity of intention.
    """
    history = agent.action_history
    if not history:
        return []

    config = agent.scarcity_model.config
    parts = ["YOUR BEHAVIORAL SUMMARY:"]

    # Mechanism usage counts over the rolling window
    recent = history[-window:]
    usage: dict[str, int] = {}
    for a in recent:
        mech = a.get("mechanism", "custom")
        usage[mech] = usage.get(mech, 0) + 1

    ranked = sorted(usage.items(), key=lambda x: x[1], reverse=True)
    usage_str = ", ".join(f"{m} ({c})" for m, c in ranked)
    parts.append(f"  Mechanism usage (last {len(recent)} cycles): {usage_str}")

    # Scarcity trajectory
    first_cycle = history[0].get("cycle", 0)
    current_cycle = history[-1].get("cycle", 0)
    first_scarcity = config.material_scarcity_at(first_cycle)
    current_scarcity = config.material_scarcity_at(current_cycle)
    parts.append(
        f"  Scarcity trajectory: {first_scarcity:.2f} (cycle {first_cycle})"
        f" -> {current_scarcity:.2f} (cycle {current_cycle})"
    )

    # Abandoned mechanisms — used at some point but not in the recent window
    all_used: set[str] = set()
    last_use_cycle: dict[str, int] = {}
    for a in history:
        mech = a.get("mechanism", "custom")
        cycle = a.get("cycle", 0)
        all_used.add(mech)
        last_use_cycle[mech] = cycle

    recent_used = set(usage.keys())
    abandoned = all_used - recent_used
    if abandoned:
        abandon_parts = []
        for m in sorted(abandoned):
            last_c = last_use_cycle[m]
            scarcity_then = config.material_scarcity_at(last_c)
            abandon_parts.append(f"{m} (last used cycle {last_c}, scarcity was {scarcity_then:.2f})")
        parts.append(f"  Abandoned mechanisms: {', '.join(abandon_parts)}")

    # Never-used mechanisms
    never_used = set(MECHANISMS) - all_used
    if never_used:
        parts.append(f"  Never used: {', '.join(sorted(never_used))}")

    return parts


def _build_neighborhood_summary(observations: dict[str, Any], window: int = 20) -> list[str]:
    """Build a summary of neighborhood behavioral trends.

    Aggregates mechanism usage across all neighbors' histories to show
    what the local community is doing — enabling agents to detect and
    respond to collective shifts.
    """
    histories = observations.get("neighbor_histories", [])
    if not histories:
        return []

    # Aggregate mechanism usage across all neighbors over the window
    usage: dict[str, int] = {}
    total = 0
    for hist in histories:
        for a in hist[-window:]:
            mech = a.get("mechanism", "custom")
            usage[mech] = usage.get(mech, 0) + 1
            total += 1

    if not total:
        return []

    parts = ["NEIGHBORHOOD TRENDS (your neighbors' recent behavior):"]
    ranked = sorted(usage.items(), key=lambda x: x[1], reverse=True)
    trend_str = ", ".join(f"{m} ({c}/{total})" for m, c in ranked)
    parts.append(f"  Mechanism usage: {trend_str}")

    # Mechanisms no neighbor is using anymore
    all_ever: set[str] = set()
    for hist in histories:
        for a in hist:
            all_ever.add(a.get("mechanism", "custom"))
    recent_used = set(usage.keys())
    community_abandoned = all_ever - recent_used
    if community_abandoned:
        parts.append(f"  No neighbor is currently using: {', '.join(sorted(community_abandoned))}")

    return parts


def _build_user_prompt(agent: CoordinationAgent, observations: dict[str, Any]) -> str:
    """Construct the per-cycle user prompt from agent state and observations."""
    persona = agent.persona
    parts = [
        f"CYCLE: {observations['cycle']}",
        f"PHASE: {observations['phase']}",
        f"MATERIAL SCARCITY: {observations['material_scarcity']:.2f}",
        "",
        "YOUR PERSONA:",
        persona.describe() if persona else "unknown",
        "",
        "GOODS SCARCITY LEVELS:",
    ]

    for good, level in observations["goods"].items():
        parts.append(f"  {good}: {level:.2f}")

    parts.append("")
    parts.append(f"YOUR NEIGHBORS: {observations['neighbor_ids']}")

    if observations["neighbor_recent_actions"]:
        parts.append("")
        parts.append("NEIGHBOR RECENT ACTIONS (this cycle so far):")
        for a in observations["neighbor_recent_actions"]:
            parts.append(
                f"  Agent {a.get('agent_id')}: {a.get('mechanism')}/{a.get('action_type')} "
                f"on {a.get('target_good', '?')}"
            )

    if observations["own_recent_actions"]:
        parts.append("")
        parts.append("YOUR RECENT ACTIONS (last few cycles):")
        for a in observations["own_recent_actions"]:
            parts.append(
                f"  Cycle {a.get('cycle')}: {a.get('mechanism')}/{a.get('action_type')} "
                f"on {a.get('target_good', '?')}"
            )

    # Behavioral summary — self-reflection from full history
    summary = _build_behavioral_summary(agent)
    if summary:
        parts.append("")
        parts.extend(summary)

    # Neighborhood trends — what the local community is doing
    neighborhood = _build_neighborhood_summary(observations)
    if neighborhood:
        parts.append("")
        parts.extend(neighborhood)

    return "\n".join(parts)


def _parse_action_response(raw: str) -> dict[str, Any] | None:
    """Parse the LLM response into a structured action dict.

    Args:
        raw: Raw text response from the LLM.

    Returns:
        Parsed action dict, or None if parsing fails.
    """
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last fence lines
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON: %s", text[:200])
        return None

    # Validate required fields
    mechanism = data.get("mechanism", "custom")
    action_type = data.get("action_type", "custom")

    # Validate mechanism
    if mechanism not in ACTION_VOCABULARY:
        mechanism = "custom"

    # Validate action_type belongs to mechanism
    if action_type not in ACTION_VOCABULARY.get(mechanism, []):
        if mechanism != "custom":
            logger.warning(
                "Action type '%s' invalid for mechanism '%s', falling back to custom",
                action_type,
                mechanism,
            )
            mechanism = "custom"
            action_type = "custom"

    return {
        "mechanism": mechanism,
        "action_type": action_type,
        "target_good": data.get("target_good"),
        "counterparty": data.get("counterparty"),
        "reasoning": data.get("reasoning", ""),
        "details": data.get("details", {}),
    }


class AgentReasoner:
    """Handles all LLM API communication for agent decision-making.

    Singleton — use AgentReasoner.get_instance() to access.
    Supports both sync (decide) and async (async_decide) operation.
    """

    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY", "")
        self.base_url = os.getenv("XAI_API_BASE_URL", "https://api.x.ai/v1")
        self.model = os.getenv("XAI_MODEL")
        if not self.model:
            raise ValueError("XAI_MODEL not set in environment")

        if not self.api_key:
            raise ValueError("XAI_API_KEY not set in environment")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0,
        )
        self.async_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0,
        )
        self._call_count = 0

        # Concurrency control: semaphore limits simultaneous async calls
        max_concurrent = int(os.getenv("XAI_MAX_CONCURRENT", "10"))
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._max_retries = 3

    @classmethod
    def get_instance(cls) -> AgentReasoner:
        """Return the singleton AgentReasoner instance."""
        global _reasoner_instance
        if _reasoner_instance is None:
            _reasoner_instance = cls()
        return _reasoner_instance

    @classmethod
    def reset(cls):
        """Reset singleton — for testing."""
        global _reasoner_instance
        if _reasoner_instance is not None:
            _reasoner_instance.client.close()
            _reasoner_instance = None

    def _build_payload(self, agent: CoordinationAgent, observations: dict[str, Any]) -> dict:
        """Build the API request payload for an agent decision."""
        user_prompt = _build_user_prompt(agent, observations)
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 300,
        }

    def decide(
        self, agent: CoordinationAgent, observations: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Call the LLM synchronously to decide an agent's action for this cycle.

        Args:
            agent: The agent making the decision.
            observations: Environment observations from agent.observe().

        Returns:
            Structured action dict, or None if the call fails.
        """
        payload = self._build_payload(agent, observations)

        try:
            response = self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            self._call_count += 1

            data = response.json()
            raw_content = data["choices"][0]["message"]["content"]
            return _parse_action_response(raw_content)

        except httpx.HTTPStatusError as e:
            logger.error("xAI API error: %s %s", e.response.status_code, e.response.text[:200])
            return None
        except (httpx.RequestError, KeyError, IndexError) as e:
            logger.error("xAI API request failed: %s", e)
            return None

    async def async_decide(
        self, agent: CoordinationAgent, observations: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Call the LLM asynchronously with semaphore concurrency control and retry.

        Retries transient errors (503, 429, timeouts) up to max_retries times
        with exponential backoff + jitter. The semaphore limits how many calls
        are in-flight simultaneously to avoid overwhelming the API.

        Args:
            agent: The agent making the decision.
            observations: Environment observations from agent.observe().

        Returns:
            Structured action dict, or None if all retries fail.
        """
        payload = self._build_payload(agent, observations)

        async with self._semaphore:
            for attempt in range(self._max_retries + 1):
                try:
                    response = await self.async_client.post(
                        "/chat/completions", json=payload
                    )
                    response.raise_for_status()
                    self._call_count += 1

                    data = response.json()
                    raw_content = data["choices"][0]["message"]["content"]
                    return _parse_action_response(raw_content)

                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    if status in (429, 503) and attempt < self._max_retries:
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(
                            "xAI API %d (attempt %d/%d), retrying in %.1fs",
                            status, attempt + 1, self._max_retries + 1, delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    logger.error(
                        "xAI API error: %s %s", status, e.response.text[:200]
                    )
                    return None
                except httpx.RequestError as e:
                    if attempt < self._max_retries:
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(
                            "xAI request error (attempt %d/%d): %s, retrying in %.1fs",
                            attempt + 1, self._max_retries + 1, e, delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    logger.error("xAI API request failed after retries: %s", e)
                    return None
                except (KeyError, IndexError) as e:
                    logger.error("xAI API response parse error: %s", e)
                    return None

        return None  # unreachable, but satisfies type checker

    @property
    def call_count(self) -> int:
        return self._call_count

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

import json
import logging
import os
from typing import TYPE_CHECKING, Any

import httpx
from dotenv import load_dotenv

from src.agent import ACTION_VOCABULARY

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
3. Consider the current scarcity level — abundant goods need less coordination.
4. Consider your persona traits when deciding strategy.
5. Respond ONLY with the JSON object. No other text.\
"""


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
    """

    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY", "")
        self.base_url = os.getenv("XAI_API_BASE_URL", "https://api.x.ai/v1")
        self.model = os.getenv("XAI_MODEL", "grok-4-fast")

        if not self.api_key:
            raise ValueError("XAI_API_KEY not set in environment")

        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        self._call_count = 0

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

    def decide(
        self, agent: CoordinationAgent, observations: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Call the LLM to decide an agent's action for this cycle.

        Args:
            agent: The agent making the decision.
            observations: Environment observations from agent.observe().

        Returns:
            Structured action dict, or None if the call fails.
        """
        user_prompt = _build_user_prompt(agent, observations)

        try:
            response = self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 300,
                },
            )
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

    @property
    def call_count(self) -> int:
        return self._call_count

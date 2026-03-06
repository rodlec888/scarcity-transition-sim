"""
@file test_reasoner.py
@description Tests for AgentReasoner, prompt construction, and response parsing.
    All tests use mocked httpx — ZERO real API calls.
@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-03-05
@changelog
- 2026-03-05: v1.0.0 - Initial creation
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from src.agent import Persona
from src.reasoner import (
    SYSTEM_PROMPT,
    AgentReasoner,
    _build_user_prompt,
    _parse_action_response,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_agent(persona: Persona | None = None) -> MagicMock:
    """Create a minimal mock of CoordinationAgent for prompt building."""
    agent = MagicMock()
    agent.persona = persona or Persona(0.5, 0.5, 0.5, 0.5, 0.5)
    agent.unique_id = 1
    agent.node_id = 0
    return agent


def _make_observations(**overrides: Any) -> dict[str, Any]:
    defaults = {
        "cycle": 5,
        "phase": "baseline",
        "material_scarcity": 1.0,
        "goods": {"food_shelter": 1.0, "attention": 1.0},
        "neighbor_ids": [1, 2],
        "neighbor_recent_actions": [],
        "own_recent_actions": [],
    }
    defaults.update(overrides)
    return defaults


def _valid_action_json(**overrides: Any) -> str:
    action = {
        "mechanism": "price",
        "action_type": "bid",
        "target_good": "food_shelter",
        "counterparty": None,
        "reasoning": "testing",
        "details": {},
    }
    action.update(overrides)
    return json.dumps(action)


# ---------------------------------------------------------------------------
# _build_user_prompt
# ---------------------------------------------------------------------------

class TestBuildUserPrompt:

    def test_includes_cycle(self):
        prompt = _build_user_prompt(_make_fake_agent(), _make_observations(cycle=42))
        assert "CYCLE: 42" in prompt

    def test_includes_phase(self):
        prompt = _build_user_prompt(_make_fake_agent(), _make_observations(phase="transition"))
        assert "PHASE: transition" in prompt

    def test_includes_persona(self):
        persona = Persona(0.9, 0.1, 0.5, 0.7, 0.3)
        prompt = _build_user_prompt(_make_fake_agent(persona), _make_observations())
        assert "YOUR PERSONA:" in prompt
        assert "0.90" in prompt  # work_identity value in describe()

    def test_includes_goods(self):
        obs = _make_observations(goods={"food_shelter": 0.75, "attention": 1.0})
        prompt = _build_user_prompt(_make_fake_agent(), obs)
        assert "food_shelter: 0.75" in prompt
        assert "attention: 1.00" in prompt

    def test_includes_neighbors(self):
        obs = _make_observations(neighbor_ids=[3, 7])
        prompt = _build_user_prompt(_make_fake_agent(), obs)
        assert "[3, 7]" in prompt

    def test_includes_neighbor_actions(self):
        obs = _make_observations(
            neighbor_recent_actions=[
                {"agent_id": 2, "mechanism": "price", "action_type": "bid", "target_good": "food_shelter"}
            ]
        )
        prompt = _build_user_prompt(_make_fake_agent(), obs)
        assert "NEIGHBOR RECENT ACTIONS" in prompt
        assert "price/bid" in prompt

    def test_includes_own_recent_actions(self):
        obs = _make_observations(
            own_recent_actions=[
                {"cycle": 3, "mechanism": "money", "action_type": "pay", "target_good": "food_shelter"}
            ]
        )
        prompt = _build_user_prompt(_make_fake_agent(), obs)
        assert "YOUR RECENT ACTIONS" in prompt
        assert "money/pay" in prompt

    def test_omits_sections_when_empty(self):
        obs = _make_observations(neighbor_recent_actions=[], own_recent_actions=[])
        prompt = _build_user_prompt(_make_fake_agent(), obs)
        assert "NEIGHBOR RECENT ACTIONS" not in prompt
        assert "YOUR RECENT ACTIONS" not in prompt


# ---------------------------------------------------------------------------
# _parse_action_response
# ---------------------------------------------------------------------------

class TestParseActionResponse:

    def test_valid_json(self):
        raw = _valid_action_json()
        result = _parse_action_response(raw)
        assert result is not None
        assert result["mechanism"] == "price"
        assert result["action_type"] == "bid"

    def test_json_with_code_fences(self):
        raw = "```json\n" + _valid_action_json() + "\n```"
        result = _parse_action_response(raw)
        assert result is not None
        assert result["mechanism"] == "price"

    def test_json_with_plain_fences(self):
        raw = "```\n" + _valid_action_json() + "\n```"
        result = _parse_action_response(raw)
        assert result is not None
        assert result["mechanism"] == "price"

    def test_invalid_json_returns_none(self):
        result = _parse_action_response("this is not json at all")
        assert result is None

    def test_empty_string_returns_none(self):
        result = _parse_action_response("")
        assert result is None

    def test_invalid_mechanism_falls_back_to_custom(self):
        raw = _valid_action_json(mechanism="barter", action_type="trade")
        result = _parse_action_response(raw)
        assert result is not None
        assert result["mechanism"] == "custom"

    def test_invalid_action_type_falls_back_to_custom(self):
        raw = _valid_action_json(mechanism="price", action_type="haggle")
        result = _parse_action_response(raw)
        assert result is not None
        assert result["mechanism"] == "custom"
        assert result["action_type"] == "custom"

    def test_missing_mechanism_defaults_to_custom(self):
        raw = json.dumps({"action_type": "custom", "reasoning": "test"})
        result = _parse_action_response(raw)
        assert result is not None
        assert result["mechanism"] == "custom"

    def test_preserves_optional_fields(self):
        raw = _valid_action_json(
            target_good="information",
            counterparty=5,
            reasoning="strategic bid",
            details={"amount": 10},
        )
        result = _parse_action_response(raw)
        assert result["target_good"] == "information"
        assert result["counterparty"] == 5
        assert result["reasoning"] == "strategic bid"
        assert result["details"] == {"amount": 10}


# ---------------------------------------------------------------------------
# AgentReasoner singleton
# ---------------------------------------------------------------------------

class TestAgentReasonerSingleton:

    def test_get_instance_returns_same_object(self, monkeypatch):
        monkeypatch.setenv("XAI_API_KEY", "test-key-123")
        import src.reasoner as mod

        # Reset to None so we can test fresh creation
        mod._reasoner_instance = None
        try:
            r1 = AgentReasoner.get_instance()
            r2 = AgentReasoner.get_instance()
            assert r1 is r2
        finally:
            # Clean up
            mod._reasoner_instance.client.close()
            mod._reasoner_instance = None

    def test_reset_creates_new_instance(self, monkeypatch):
        monkeypatch.setenv("XAI_API_KEY", "test-key-123")
        import src.reasoner as mod

        mod._reasoner_instance = None
        try:
            r1 = AgentReasoner.get_instance()
            AgentReasoner.reset()
            assert mod._reasoner_instance is None
            r2 = AgentReasoner.get_instance()
            assert r1 is not r2
        finally:
            if mod._reasoner_instance:
                mod._reasoner_instance.client.close()
            mod._reasoner_instance = None

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("XAI_API_KEY", raising=False)
        import src.reasoner as mod

        mod._reasoner_instance = None
        with pytest.raises(ValueError, match="XAI_API_KEY"):
            AgentReasoner()


# ---------------------------------------------------------------------------
# AgentReasoner.decide() — mocked httpx
# ---------------------------------------------------------------------------

class TestAgentReasonerDecide:

    @pytest.fixture()
    def reasoner(self, monkeypatch):
        """Create a real AgentReasoner with mocked httpx client."""
        monkeypatch.setenv("XAI_API_KEY", "test-key-123")
        import src.reasoner as mod

        mod._reasoner_instance = None
        r = AgentReasoner()
        yield r
        r.client.close()
        mod._reasoner_instance = None

    def _mock_response(self, content: str, status_code: int = 200) -> MagicMock:
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = status_code
        resp.json.return_value = {
            "choices": [{"message": {"content": content}}]
        }
        resp.raise_for_status = MagicMock()
        if status_code >= 400:
            resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "error", request=MagicMock(), response=resp
            )
            resp.text = "error body"
        return resp

    def test_decide_success(self, reasoner):
        action_json = _valid_action_json()
        reasoner.client.post = MagicMock(return_value=self._mock_response(action_json))

        agent = _make_fake_agent()
        obs = _make_observations()
        result = reasoner.decide(agent, obs)

        assert result is not None
        assert result["mechanism"] == "price"
        assert result["action_type"] == "bid"
        assert reasoner.call_count == 1

    def test_decide_http_error_returns_none(self, reasoner):
        reasoner.client.post = MagicMock(return_value=self._mock_response("", status_code=403))

        agent = _make_fake_agent()
        obs = _make_observations()
        result = reasoner.decide(agent, obs)

        assert result is None

    def test_decide_network_error_returns_none(self, reasoner):
        reasoner.client.post = MagicMock(side_effect=httpx.RequestError("connection failed"))

        agent = _make_fake_agent()
        obs = _make_observations()
        result = reasoner.decide(agent, obs)

        assert result is None

    def test_decide_invalid_json_response_returns_none(self, reasoner):
        reasoner.client.post = MagicMock(
            return_value=self._mock_response("I cannot help you with that.")
        )

        agent = _make_fake_agent()
        obs = _make_observations()
        result = reasoner.decide(agent, obs)

        assert result is None

    def test_decide_calls_api_with_correct_payload(self, reasoner):
        action_json = _valid_action_json()
        reasoner.client.post = MagicMock(return_value=self._mock_response(action_json))

        agent = _make_fake_agent()
        obs = _make_observations(cycle=10, phase="transition")
        reasoner.decide(agent, obs)

        call_args = reasoner.client.post.call_args
        assert call_args[0][0] == "/chat/completions"
        payload = call_args[1]["json"]
        assert payload["model"] == reasoner.model
        assert payload["temperature"] == 0.7
        messages = payload["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT
        assert messages[1]["role"] == "user"
        assert "CYCLE: 10" in messages[1]["content"]


# ---------------------------------------------------------------------------
# SYSTEM_PROMPT sanity
# ---------------------------------------------------------------------------

class TestSystemPrompt:

    def test_mentions_all_mechanisms(self):
        for mech in ("price", "money", "property", "employment", "taxation", "reputation", "queuing", "custom"):
            assert mech in SYSTEM_PROMPT

    def test_mentions_json(self):
        assert "JSON" in SYSTEM_PROMPT or "json" in SYSTEM_PROMPT

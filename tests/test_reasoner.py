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

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.agent import Persona
from src.config import SimConfig
from src.reasoner import (
    SYSTEM_PROMPT,
    AgentReasoner,
    _build_behavioral_summary,
    _build_neighborhood_summary,
    _build_user_prompt,
    _parse_action_response,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_agent(
    persona: Persona | None = None,
    action_history: list[dict[str, Any]] | None = None,
) -> MagicMock:
    """Create a minimal mock of CoordinationAgent for prompt building."""
    agent = MagicMock()
    agent.persona = persona or Persona(0.5, 0.5, 0.5, 0.5, 0.5)
    agent.unique_id = 1
    agent.node_id = 0
    agent.action_history = action_history or []
    agent.scarcity_model.config = SimConfig()
    return agent


def _make_observations(**overrides: Any) -> dict[str, Any]:
    defaults = {
        "cycle": 5,
        "phase": "baseline",
        "material_scarcity": 1.0,
        "goods": {"food_shelter": 1.0, "attention": 1.0},
        "neighbor_ids": [1, 2],
        "neighbor_recent_actions": [],
        "neighbor_histories": [],
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
# _build_behavioral_summary
# ---------------------------------------------------------------------------

class TestBuildBehavioralSummary:

    def test_empty_history_returns_empty(self):
        agent = _make_fake_agent()
        assert _build_behavioral_summary(agent) == []

    def test_includes_mechanism_usage(self):
        history = [
            {"mechanism": "price", "cycle": i, "target_good": "food"}
            for i in range(5)
        ]
        agent = _make_fake_agent(action_history=history)
        lines = _build_behavioral_summary(agent)
        joined = "\n".join(lines)
        assert "Mechanism usage" in joined
        assert "price (5)" in joined

    def test_includes_scarcity_trajectory(self):
        history = [
            {"mechanism": "price", "cycle": 0, "target_good": "food"},
            {"mechanism": "price", "cycle": 100, "target_good": "food"},
        ]
        agent = _make_fake_agent(action_history=history)
        lines = _build_behavioral_summary(agent)
        joined = "\n".join(lines)
        assert "Scarcity trajectory" in joined
        assert "cycle 0" in joined
        assert "cycle 100" in joined

    def test_detects_abandoned_mechanisms(self):
        history = [
            {"mechanism": "price", "cycle": 0, "target_good": "food"},
        ] + [
            {"mechanism": "employment", "cycle": i, "target_good": "labor"}
            for i in range(1, 25)
        ]
        agent = _make_fake_agent(action_history=history)
        lines = _build_behavioral_summary(agent)
        joined = "\n".join(lines)
        assert "Abandoned mechanisms" in joined
        assert "price" in joined

    def test_detects_never_used(self):
        history = [
            {"mechanism": "employment", "cycle": i, "target_good": "labor"}
            for i in range(3)
        ]
        agent = _make_fake_agent(action_history=history)
        lines = _build_behavioral_summary(agent)
        joined = "\n".join(lines)
        assert "Never used" in joined
        assert "price" in joined

    def test_appears_in_user_prompt(self):
        history = [
            {"mechanism": "price", "cycle": i, "target_good": "food"}
            for i in range(3)
        ]
        agent = _make_fake_agent(action_history=history)
        obs = _make_observations()
        prompt = _build_user_prompt(agent, obs)
        assert "YOUR BEHAVIORAL SUMMARY:" in prompt


# ---------------------------------------------------------------------------
# _build_neighborhood_summary
# ---------------------------------------------------------------------------

class TestBuildNeighborhoodSummary:

    def test_empty_histories_returns_empty(self):
        obs = _make_observations(neighbor_histories=[])
        assert _build_neighborhood_summary(obs) == []

    def test_includes_mechanism_usage(self):
        neighbor1 = [{"mechanism": "price", "cycle": i} for i in range(5)]
        neighbor2 = [{"mechanism": "employment", "cycle": i} for i in range(3)]
        obs = _make_observations(neighbor_histories=[neighbor1, neighbor2])
        lines = _build_neighborhood_summary(obs)
        joined = "\n".join(lines)
        assert "NEIGHBORHOOD TRENDS" in joined
        assert "price (5/8)" in joined
        assert "employment (3/8)" in joined

    def test_detects_community_abandoned(self):
        # Neighbor used money early, then only employment recently
        neighbor = (
            [{"mechanism": "money", "cycle": 0}]
            + [{"mechanism": "employment", "cycle": i} for i in range(1, 25)]
        )
        obs = _make_observations(neighbor_histories=[neighbor])
        lines = _build_neighborhood_summary(obs)
        joined = "\n".join(lines)
        assert "No neighbor is currently using" in joined
        assert "money" in joined

    def test_appears_in_user_prompt(self):
        neighbor = [{"mechanism": "price", "cycle": i} for i in range(3)]
        agent = _make_fake_agent()
        obs = _make_observations(neighbor_histories=[neighbor])
        prompt = _build_user_prompt(agent, obs)
        assert "NEIGHBORHOOD TRENDS" in prompt


# ---------------------------------------------------------------------------
# SYSTEM_PROMPT sanity
# ---------------------------------------------------------------------------

class TestSystemPrompt:

    def test_mentions_all_mechanisms(self):
        for mech in ("price", "money", "property", "employment", "taxation", "reputation", "queuing", "custom"):
            assert mech in SYSTEM_PROMPT

    def test_mentions_json(self):
        assert "JSON" in SYSTEM_PROMPT or "json" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# AgentReasoner.async_decide() — mocked httpx.AsyncClient
# ---------------------------------------------------------------------------

class TestAgentReasonerAsyncDecide:

    @pytest.fixture()
    def reasoner(self, monkeypatch):
        """Create a real AgentReasoner with mocked async client."""
        monkeypatch.setenv("XAI_API_KEY", "test-key-123")
        import src.reasoner as mod

        mod._reasoner_instance = None
        r = AgentReasoner()
        yield r
        r.client.close()
        mod._reasoner_instance = None

    def _mock_async_response(self, content: str, status_code: int = 200) -> MagicMock:
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

    @pytest.mark.asyncio
    async def test_async_decide_success(self, reasoner):
        action_json = _valid_action_json()
        reasoner.async_client.post = AsyncMock(
            return_value=self._mock_async_response(action_json)
        )

        agent = _make_fake_agent()
        obs = _make_observations()
        result = await reasoner.async_decide(agent, obs)

        assert result is not None
        assert result["mechanism"] == "price"
        assert result["action_type"] == "bid"
        assert reasoner.call_count == 1

    @pytest.mark.asyncio
    async def test_async_decide_http_error_returns_none(self, reasoner):
        reasoner.async_client.post = AsyncMock(
            return_value=self._mock_async_response("", status_code=403)
        )

        agent = _make_fake_agent()
        obs = _make_observations()
        result = await reasoner.async_decide(agent, obs)

        assert result is None

    @pytest.mark.asyncio
    async def test_async_decide_network_error_returns_none(self, reasoner):
        reasoner.async_client.post = AsyncMock(
            side_effect=httpx.RequestError("connection failed")
        )

        agent = _make_fake_agent()
        obs = _make_observations()
        result = await reasoner.async_decide(agent, obs)

        assert result is None

    @pytest.mark.asyncio
    async def test_async_decide_invalid_json_returns_none(self, reasoner):
        reasoner.async_client.post = AsyncMock(
            return_value=self._mock_async_response("I cannot help you with that.")
        )

        agent = _make_fake_agent()
        obs = _make_observations()
        result = await reasoner.async_decide(agent, obs)

        assert result is None

    @pytest.mark.asyncio
    async def test_async_decide_concurrent_calls(self, reasoner):
        """Multiple async_decide calls run concurrently via asyncio.gather."""
        action_json = _valid_action_json()
        reasoner.async_client.post = AsyncMock(
            return_value=self._mock_async_response(action_json)
        )

        agents_obs = [
            (_make_fake_agent(), _make_observations(cycle=i))
            for i in range(5)
        ]
        tasks = [
            reasoner.async_decide(agent, obs)
            for agent, obs in agents_obs
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r is not None for r in results)
        assert all(r["mechanism"] == "price" for r in results)
        assert reasoner.call_count == 5

    @pytest.mark.asyncio
    async def test_async_decide_uses_same_payload_as_sync(self, reasoner):
        """Verify async_decide sends identical payload to sync decide."""
        action_json = _valid_action_json()
        reasoner.async_client.post = AsyncMock(
            return_value=self._mock_async_response(action_json)
        )

        agent = _make_fake_agent()
        obs = _make_observations(cycle=10, phase="transition")
        await reasoner.async_decide(agent, obs)

        call_args = reasoner.async_client.post.call_args
        assert call_args[0][0] == "/chat/completions"
        payload = call_args[1]["json"]
        assert payload["model"] == reasoner.model
        assert payload["temperature"] == 0.7
        messages = payload["messages"]
        assert messages[0]["content"] == SYSTEM_PROMPT
        assert "CYCLE: 10" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_async_decide_retries_on_503(self, reasoner, monkeypatch):
        """503 triggers retry with backoff, succeeds on second attempt."""
        monkeypatch.setattr("src.reasoner.random.uniform", lambda a, b: 0)
        monkeypatch.setattr("src.reasoner.asyncio.sleep", AsyncMock())

        action_json = _valid_action_json()
        error_resp = self._mock_async_response("", status_code=503)
        ok_resp = self._mock_async_response(action_json)
        reasoner.async_client.post = AsyncMock(side_effect=[error_resp, ok_resp])

        agent = _make_fake_agent()
        obs = _make_observations()
        result = await reasoner.async_decide(agent, obs)

        assert result is not None
        assert result["mechanism"] == "price"
        assert reasoner.async_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_async_decide_retries_on_429(self, reasoner, monkeypatch):
        """429 triggers retry with backoff, succeeds on second attempt."""
        monkeypatch.setattr("src.reasoner.random.uniform", lambda a, b: 0)
        monkeypatch.setattr("src.reasoner.asyncio.sleep", AsyncMock())

        action_json = _valid_action_json()
        error_resp = self._mock_async_response("", status_code=429)
        ok_resp = self._mock_async_response(action_json)
        reasoner.async_client.post = AsyncMock(side_effect=[error_resp, ok_resp])

        agent = _make_fake_agent()
        obs = _make_observations()
        result = await reasoner.async_decide(agent, obs)

        assert result is not None
        assert reasoner.async_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_async_decide_exhausts_retries_returns_none(self, reasoner, monkeypatch):
        """All retries fail -> returns None."""
        monkeypatch.setattr("src.reasoner.random.uniform", lambda a, b: 0)
        monkeypatch.setattr("src.reasoner.asyncio.sleep", AsyncMock())

        error_resp = self._mock_async_response("", status_code=503)
        reasoner.async_client.post = AsyncMock(
            side_effect=[error_resp, error_resp, error_resp, error_resp]
        )

        agent = _make_fake_agent()
        obs = _make_observations()
        result = await reasoner.async_decide(agent, obs)

        assert result is None
        # 1 initial + 3 retries = 4 attempts
        assert reasoner.async_client.post.call_count == 4

    @pytest.mark.asyncio
    async def test_async_decide_no_retry_on_400(self, reasoner):
        """Non-retryable errors (400, 403) fail immediately without retry."""
        error_resp = self._mock_async_response("", status_code=400)
        reasoner.async_client.post = AsyncMock(return_value=error_resp)

        agent = _make_fake_agent()
        obs = _make_observations()
        result = await reasoner.async_decide(agent, obs)

        assert result is None
        assert reasoner.async_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_async_decide_retries_network_error(self, reasoner, monkeypatch):
        """Network errors are retried."""
        monkeypatch.setattr("src.reasoner.random.uniform", lambda a, b: 0)
        monkeypatch.setattr("src.reasoner.asyncio.sleep", AsyncMock())

        action_json = _valid_action_json()
        ok_resp = self._mock_async_response(action_json)
        reasoner.async_client.post = AsyncMock(
            side_effect=[httpx.RequestError("timeout"), ok_resp]
        )

        agent = _make_fake_agent()
        obs = _make_observations()
        result = await reasoner.async_decide(agent, obs)

        assert result is not None
        assert reasoner.async_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_async_decide_semaphore_limits_concurrency(self, reasoner):
        """Semaphore limits how many calls are in-flight simultaneously."""
        reasoner._semaphore = asyncio.Semaphore(2)
        max_concurrent = 0
        current = 0

        action_json = _valid_action_json()

        async def _tracked_post(*args, **kwargs):
            nonlocal current, max_concurrent
            current += 1
            max_concurrent = max(max_concurrent, current)
            await asyncio.sleep(0.01)
            current -= 1
            return self._mock_async_response(action_json)

        reasoner.async_client.post = _tracked_post

        tasks = [
            reasoner.async_decide(_make_fake_agent(), _make_observations(cycle=i))
            for i in range(6)
        ]
        results = await asyncio.gather(*tasks)

        assert all(r is not None for r in results)
        assert max_concurrent <= 2

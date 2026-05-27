import pytest
from unittest.mock import patch, MagicMock
from hyperion_task.agents.base import BaseAgent
from hyperion_task.utils.exceptions import RateLimitExceeded
from hyperion_task.utils.circuit_breaker import CircuitState, CircuitOpenError

class DummyAgent(BaseAgent):
    async def process(self, task, context):
        return {"success": True}

@pytest.mark.asyncio
async def test_think_rate_limiting():
    agent = DummyAgent("test", "testing")
    with patch.object(agent._rate_limiter, 'wait_and_acquire', return_value=False):
        with pytest.raises(RateLimitExceeded):
            await agent.think("test")

@pytest.mark.asyncio
async def test_think_circuit_breaker_open():
    agent = DummyAgent("test", "testing")
    with patch.object(agent._circuit_breaker, 'call', side_effect=CircuitOpenError("Open")):
        result = await agent.think("test")
        assert result == ""

@pytest.mark.asyncio
async def test_think_success():
    agent = DummyAgent("test", "testing")
    mock_response = MagicMock()
    mock_response.response = "ok"
    with patch.object(agent._client, 'generate', return_value=mock_response):
        result = await agent.think("test")
        assert result == "ok"
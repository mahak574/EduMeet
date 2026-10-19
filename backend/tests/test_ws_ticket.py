import json
import pytest
import pytest_asyncio
from app.core.websocket_ticket import issue_ws_ticket, consume_ws_ticket
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_websocket_ticket_issuance_and_consumption():
    mock_redis = AsyncMock()
    stored_data = {}

    async def mock_setex(key, ttl, val):
        stored_data[key] = val

    async def mock_execute_command(cmd, key):
        if cmd == "GETDEL":
            return stored_data.pop(key, None)
        return None

    mock_redis.setex = mock_setex
    mock_redis.execute_command = mock_execute_command

    with patch("app.core.websocket_ticket.get_redis", return_value=mock_redis):
        user_id = "6713cf8e2c39a2b5e4f1a001"
        session_id = "6713cf8e2c39a2b5e4f1a007"
        role = "teacher_a"

        ticket = await issue_ws_ticket(user_id=user_id, session_id=session_id, role=role)
        assert len(ticket) > 20

        # First consumption should succeed
        payload = await consume_ws_ticket(ticket)
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["session_id"] == session_id
        assert payload["role"] == role

        # Second consumption of the same ticket must be None (single-use!)
        second_attempt = await consume_ws_ticket(ticket)
        assert second_attempt is None

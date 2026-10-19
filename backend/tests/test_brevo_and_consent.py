import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.services.email_service.brevo import BrevoEmailProvider


@pytest.mark.asyncio
async def test_brevo_email_provider_send_success():
    provider = BrevoEmailProvider(api_key="xkeysib-test-mock-key")
    mock_resp = httpx.Response(status_code=201, json={"messageId": "<test@brevo>"})

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        success = await provider.send_otp("student@example.com", "849201")
        assert success is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["headers"]["api-key"] == "xkeysib-test-mock-key"
        assert call_kwargs["json"]["to"] == [{"email": "student@example.com"}]
        assert "849201" in call_kwargs["json"]["subject"]


@pytest.mark.asyncio
async def test_brevo_email_provider_handles_api_failure():
    provider = BrevoEmailProvider(api_key="invalid-key")
    mock_resp = httpx.Response(status_code=401, json={"message": "Key not authorized"})

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        success = await provider.send_otp("student@example.com", "123456")
        assert success is False

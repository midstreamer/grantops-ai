from app.services.llm_service import LLMProviderError


def test_ai_health_missing_api_key(client, monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.get("/api/ai/health")
    assert response.status_code == 200
    body = response.json()
    assert body["llm_provider"] == "openai"
    assert body["api_key_configured"] is False
    assert body["ai_features_available"] is False


def test_ai_health_unsupported_provider(client, monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "unsupported-provider")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    response = client.get("/api/ai/health")
    assert response.status_code == 200
    body = response.json()
    assert body["llm_provider"] == "unsupported-provider"
    assert body["ai_features_available"] is False
    assert "Unsupported" in body["message"]


def test_ai_smoke_test_not_configured(client, monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    response = client.post(
        "/api/ai/smoke-test",
        json={"prompt": "Test prompt"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "not configured" in body["response"].lower()


def test_ai_smoke_test_provider_error(client, monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def _raise(*args, **kwargs):
        raise LLMProviderError("429 quota exceeded")

    monkeypatch.setattr("app.routers.ai.smoke_test_prompt", _raise)

    response = client.post(
        "/api/ai/smoke-test",
        json={"prompt": "Test prompt"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "quota" in body["response"].lower()

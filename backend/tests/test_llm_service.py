import pytest

from app.services.llm_service import (
    LLMNotConfiguredError,
    OpenAIProvider,
    get_llm_provider,
)


def test_get_llm_provider_missing_config(monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(LLMNotConfiguredError) as exc:
        get_llm_provider()
    assert "LLM_PROVIDER" in str(exc.value)


def test_get_llm_provider_openai_without_key(monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(LLMNotConfiguredError) as exc:
        get_llm_provider()
    assert "OPENAI_API_KEY" in str(exc.value)


def test_openai_summarize_opportunity(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"opportunity_summary":"Summary text",'
                                '"why_it_fits":"Good fit",'
                                '"concerns":"Timeline risk",'
                                '"recommended_framing":"Emphasize workforce",'
                                '"recommended_next_actions":"Draft aims",'
                                '"possible_proposal_title":"AI Cyber Training Grant"}'
                            )
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.services.llm_service.httpx.Client", FakeClient)

    provider = OpenAIProvider("test-key")
    result = provider.summarize_opportunity(
        opportunity=type("Opp", (), {
            "title": "Test",
            "agency": "NSF",
            "program": None,
            "source": "manual",
            "source_id": None,
            "deadline": None,
            "posted_date": None,
            "award_floor": None,
            "award_ceiling": None,
            "fit_score": 80,
            "recommendation": "pursue",
            "status": "review",
            "description": "Cyber AI",
            "eligibility": "Universities",
            "fit_summary": "Strong",
            "raw_data": {},
        })(),
        profile=type("Profile", (), {
            "researcher_name": "Test PI",
            "institution": "Test U",
            "primary_research_focus": "Cyber AI",
            "research_domains": ["cybersecurity"],
            "methods": ["experiments"],
            "target_funders": ["NSF"],
            "keywords": ["AI"],
            "preferred_outputs": [],
        })(),
        literature_items=[],
    )

    assert result["possible_proposal_title"] == "AI Cyber Training Grant"


def test_ai_summary_endpoint_not_configured(client, monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    created = client.post(
        "/api/opportunities",
        json={"source": "manual", "title": "Test opp"},
    )
    opp_id = created.json()["id"]

    response = client.post(f"/api/opportunities/{opp_id}/ai-summary")
    assert response.status_code == 503
    assert "LLM" in response.json()["detail"]

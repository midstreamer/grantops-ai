from unittest.mock import patch

from app.services.llm_service import (
    concept_note_markdown_has_required_sections,
    concept_note_to_markdown,
)


MOCK_CONCEPT_NOTE = {
    "working_title": "Secure AI Workforce Training",
    "problem_statement": "SOC analysts lack AI-ready skills.",
    "research_gap": "Limited empirical training evaluation.",
    "proposed_study": "Design and evaluate an AI-augmented curriculum.",
    "research_questions": "1. Does training improve detection?\n2. What skills transfer?",
    "methods": "Quasi-experimental study with pre/post assessment.",
    "expected_contributions": "Validated training framework.",
    "broader_impacts": "Stronger national cyber workforce.",
    "why_this_funder_should_care": "Aligns with NSF workforce priorities.",
    "immediate_next_steps": "Confirm partner sites and IRB timeline.",
}


def test_concept_note_markdown_has_required_sections() -> None:
    markdown = concept_note_to_markdown(MOCK_CONCEPT_NOTE)
    assert concept_note_markdown_has_required_sections(
        markdown,
        title=MOCK_CONCEPT_NOTE["working_title"],
    )
    assert not concept_note_markdown_has_required_sections(markdown, title="")


def test_concept_note_endpoint_saves_draft(client) -> None:
    created = client.post(
        "/api/opportunities",
        json={"source": "manual", "title": "Cyber workforce grant"},
    )
    assert created.status_code == 201
    opp_id = created.json()["id"]

    with patch(
        "app.routers.opportunities.draft_concept_note_structured",
        return_value=MOCK_CONCEPT_NOTE,
    ):
        response = client.post(f"/api/opportunities/{opp_id}/concept-note")

    assert response.status_code == 201
    body = response.json()
    assert body["opportunity_id"] == opp_id
    assert body["draft_type"] == "concept_note"
    assert body["title"] == "Secure AI Workforce Training"
    assert "Problem Statement" in body["content"]
    assert body["content"] == concept_note_to_markdown(MOCK_CONCEPT_NOTE)

    listed = client.get(f"/api/opportunities/{opp_id}/drafts")
    assert listed.status_code == 200
    drafts = listed.json()
    assert len(drafts) == 1
    assert drafts[0]["id"] == body["id"]

    updated = client.put(
        f"/api/opportunities/{opp_id}/drafts/{body['id']}",
        json={"title": "Updated title", "content": "# Edited\n\nNew body"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated title"
    assert updated.json()["content"] == "# Edited\n\nNew body"


def test_concept_note_endpoint_not_configured(client, monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    created = client.post(
        "/api/opportunities",
        json={"source": "manual", "title": "Test opp"},
    )
    opp_id = created.json()["id"]

    response = client.post(f"/api/opportunities/{opp_id}/concept-note")
    assert response.status_code == 503
    assert "LLM" in response.json()["detail"]

from unittest.mock import MagicMock, patch

from app.services.google_docs_service import (
    _build_doc_insert_requests,
    google_doc_url_for_id,
)


def test_google_doc_url_for_id() -> None:
    assert (
        google_doc_url_for_id("abc123")
        == "https://docs.google.com/document/d/abc123/edit"
    )


def test_build_doc_insert_requests_includes_heading_styles() -> None:
    requests = _build_doc_insert_requests(
        "My Draft",
        "## Problem Statement\n\nA clear gap exists.\n",
    )
    assert any("insertText" in request for request in requests)
    assert any("updateParagraphStyle" in request for request in requests)


def test_export_proposal_draft_to_google_doc(client) -> None:
    opp = client.post(
        "/api/opportunities",
        json={"source": "manual", "title": "Docs export opp"},
    )
    opp_id = opp.json()["id"]

    with patch(
        "app.routers.opportunities.draft_concept_note_structured",
        return_value={
            "working_title": "Doc Export Draft",
            "problem_statement": "Problem",
            "research_gap": "",
            "proposed_study": "",
            "research_questions": "",
            "methods": "",
            "expected_contributions": "",
            "broader_impacts": "",
            "why_this_funder_should_care": "",
            "immediate_next_steps": "",
        },
    ):
        draft_resp = client.post(f"/api/opportunities/{opp_id}/concept-note")

    draft_id = draft_resp.json()["id"]

    def _fake_create(db, draft_id_arg: int):
        from app.models.proposal_draft import ProposalDraft

        draft = db.get(ProposalDraft, draft_id_arg)
        assert draft is not None
        draft.google_doc_url = google_doc_url_for_id("doc-export-123")
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft

    with patch(
        "app.routers.proposal_drafts.create_google_doc_from_proposal_draft",
        side_effect=_fake_create,
    ):
        response = client.post(f"/api/proposal-drafts/{draft_id}/export/google-doc")

    assert response.status_code == 200
    body = response.json()
    assert body["google_doc_url"] == google_doc_url_for_id("doc-export-123")


def test_export_proposal_draft_not_configured(client, monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

    opp = client.post(
        "/api/opportunities",
        json={"source": "manual", "title": "Docs export opp"},
    )
    opp_id = opp.json()["id"]

    with patch(
        "app.routers.opportunities.draft_concept_note_structured",
        return_value={
            "working_title": "Draft",
            "problem_statement": "P",
            "research_gap": "",
            "proposed_study": "",
            "research_questions": "",
            "methods": "",
            "expected_contributions": "",
            "broader_impacts": "",
            "why_this_funder_should_care": "",
            "immediate_next_steps": "",
        },
    ):
        draft_id = client.post(f"/api/opportunities/{opp_id}/concept-note").json()["id"]

    response = client.post(f"/api/proposal-drafts/{draft_id}/export/google-doc")
    assert response.status_code == 503
    assert "Google" in response.json()["detail"]


def test_create_google_doc_from_proposal_draft_writes_url(client) -> None:
    from app.db.session import SessionLocal
    from app.models.proposal_draft import ProposalDraft
    from app.services.google_docs_service import create_google_doc_from_proposal_draft

    opp_id = client.post(
        "/api/opportunities",
        json={"source": "manual", "title": "Docs unit test opp"},
    ).json()["id"]

    db = SessionLocal()
    try:
        draft = ProposalDraft(
            opportunity_id=opp_id,
            title="Unit Test Draft",
            draft_type="concept_note",
            content="## Section\n\nBody text.",
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        mock_docs = MagicMock()
        mock_docs.documents.return_value.create.return_value.execute.return_value = {
            "documentId": "unit-test-doc-id",
        }
        mock_docs.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        with patch(
            "app.services.google_docs_service.get_docs_service",
            return_value=mock_docs,
        ):
            updated = create_google_doc_from_proposal_draft(db, draft.id)

        assert updated.google_doc_url == google_doc_url_for_id("unit-test-doc-id")
        mock_docs.documents.return_value.batchUpdate.assert_called_once()
    finally:
        db.close()

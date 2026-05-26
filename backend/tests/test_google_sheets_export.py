from unittest.mock import MagicMock, patch

from app.services.opportunity_export import export_row_key


def test_export_row_key_prefers_source_id() -> None:
    row = {
        "source": "grants.gov",
        "source_id": "ABC-123",
        "title": "Title A",
        "agency": "NSF",
        "deadline": "2026-01-01",
    }
    assert export_row_key(row) == "grants.gov|ABC-123"


def test_export_row_key_fallback_without_source_id() -> None:
    row = {
        "source": "manual",
        "source_id": "",
        "title": "Workforce Training",
        "agency": "NSF",
        "deadline": "2026-06-01",
    }
    assert export_row_key(row) == "workforce training|nsf|2026-06-01"


def test_google_sheets_export_endpoint(client) -> None:
    client.post(
        "/api/opportunities",
        json={
            "source": "manual",
            "source_id": "sheet-export-1",
            "title": "Sheets Export Grant",
            "agency": "NIH",
        },
    )

    with patch(
        "app.routers.export.export_opportunities_to_google_sheet",
        return_value={
            "spreadsheet_id": "test-sheet-id",
            "worksheet": "Opportunities",
            "total_rows": 1,
            "rows_updated": 0,
            "rows_appended": 1,
        },
    ):
        response = client.post("/api/export/google-sheets")

    assert response.status_code == 200
    body = response.json()
    assert body["spreadsheet_id"] == "test-sheet-id"
    assert body["worksheet"] == "Opportunities"
    assert body["total_rows"] == 1
    assert body["rows_appended"] == 1


def test_google_sheets_export_not_configured(client, monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_SHEETS_SPREADSHEET_ID", raising=False)

    response = client.post("/api/export/google-sheets")
    assert response.status_code == 503
    assert "Google Sheets" in response.json()["detail"]


def test_append_or_update_opportunity_rows() -> None:
    from app.services.google_sheets_service import append_or_update_opportunity_rows

    service = MagicMock()
    values_api = MagicMock()
    spreadsheets_api = MagicMock()
    service.spreadsheets.return_value = spreadsheets_api
    spreadsheets_api.values.return_value = values_api

    spreadsheets_api.get.return_value.execute.return_value = {
        "sheets": [{"properties": {"title": "Opportunities"}}],
    }
    values_api.get.return_value.execute.return_value = {
        "values": [
            [
                "title",
                "agency",
                "program",
                "source",
                "source_id",
                "deadline",
                "posted_date",
                "opportunity_status",
                "fit_score",
                "recommendation",
                "status",
                "next_action",
                "url",
                "fit_summary",
            ],
            [
                "Old Title",
                "NSF",
                "",
                "manual",
                "existing-1",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ],
        ],
    }

    rows = [
        {
            "title": "Updated Title",
            "agency": "NSF",
            "program": "",
            "source": "manual",
            "source_id": "existing-1",
            "deadline": "",
            "posted_date": "",
            "opportunity_status": "",
            "fit_score": "90",
            "recommendation": "pursue",
            "status": "review",
            "next_action": "",
            "url": "",
            "fit_summary": "",
        },
        {
            "title": "New Grant",
            "agency": "NIH",
            "program": "",
            "source": "manual",
            "source_id": "new-1",
            "deadline": "",
            "posted_date": "",
            "opportunity_status": "",
            "fit_score": "",
            "recommendation": "",
            "status": "",
            "next_action": "",
            "url": "",
            "fit_summary": "",
        },
    ]

    stats = append_or_update_opportunity_rows(
        service,
        "spreadsheet-123",
        rows,
        worksheet_name="Opportunities",
    )

    assert stats["rows_updated"] == 1
    assert stats["rows_appended"] == 1
    assert stats["total_rows"] == 2
    values_api.batchUpdate.assert_called_once()
    values_api.append.assert_called_once()

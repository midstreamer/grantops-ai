def test_export_opportunities_csv(client) -> None:
    client.post(
        "/api/opportunities",
        json={
            "source": "manual",
            "title": "Export Test Grant",
            "agency": "NSF",
            "program": "TEST-001",
            "deadline": "2026-12-31",
            "recommendation": "pursue",
            "status": "review",
            "fit_score": 88,
            "fit_summary": "Strong alignment",
        },
    )

    response = client.get("/api/export/opportunities.csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "grantops-opportunities.csv" in response.headers.get("content-disposition", "")

    body = response.text
    assert "title,agency,program,source,source_id" in body
    assert "Export Test Grant" in body
    assert "NSF" in body

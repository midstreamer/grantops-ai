def test_dashboard_stats(client) -> None:
    client.post(
        "/api/opportunities",
        json={
            "source": "manual",
            "title": "Cybersecurity workforce AI training",
            "agency": "NSF",
            "deadline": "2099-06-01",
            "recommendation": "pursue",
            "status": "review",
            "fit_score": 80,
        },
    )

    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_opportunities"] >= 1
    assert data["pursue_count"] >= 1
    assert "top_opportunities" in data

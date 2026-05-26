def test_opportunity_crud(client) -> None:
    create_payload = {
        "source": "manual",
        "source_id": "local-1",
        "title": "Test Opportunity",
        "agency": "NSF",
        "program": "Secure and Trustworthy Cyberspace",
        "description": "A test opportunity",
        "eligibility": "US institutions",
        "award_ceiling": 1000000,
        "award_floor": 100000,
        "deadline": "2026-12-31",
        "posted_date": "2026-05-01",
        "opportunity_status": "open",
        "url": "https://example.com/opportunity",
        "raw_data": {"hello": "world"},
        "fit_score": 75,
        "fit_summary": "Looks promising",
        "recommendation": "monitor",
        "status": "review",
        "next_action": "Read solicitation PDF",
    }

    created = client.post("/api/opportunities", json=create_payload)
    assert created.status_code == 201
    created_data = created.json()
    opp_id = created_data["id"]
    assert created_data["title"] == "Test Opportunity"

    listed = client.get("/api/opportunities")
    assert listed.status_code == 200
    assert any(o["id"] == opp_id for o in listed.json())

    fetched = client.get(f"/api/opportunities/{opp_id}")
    assert fetched.status_code == 200
    assert fetched.json()["agency"] == "NSF"

    updated = client.put(
        f"/api/opportunities/{opp_id}",
        json={"status": "pursuing", "next_action": "Draft aims"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "pursuing"
    assert updated.json()["next_action"] == "Draft aims"

    deleted = client.delete(f"/api/opportunities/{opp_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/opportunities/{opp_id}")
    assert missing.status_code == 404


def test_score_endpoints(client) -> None:
    created = client.post(
        "/api/opportunities",
        json={
            "source": "manual",
            "title": "AI cybersecurity workforce training program",
            "agency": "NSF",
            "description": "Experiment and simulation based evaluation for SOC decision support.",
            "eligibility": "Universities and nonprofit research institutions",
            "deadline": "2099-12-31",
            "status": "new",
            "recommendation": "unreviewed",
        },
    )
    assert created.status_code == 201
    opp_id = created.json()["id"]

    scored = client.post(f"/api/opportunities/{opp_id}/score")
    assert scored.status_code == 200
    scored_body = scored.json()
    assert scored_body["score"]["fit_score"] >= 0
    assert scored_body["score"]["recommendation"] in {"pursue", "monitor", "decline"}
    assert isinstance(scored_body["score"]["matched_keywords"], list)
    assert isinstance(scored_body["score"]["concerns"], list)
    assert isinstance(scored_body["score"]["recommended_next_action"], str)

    score_all = client.post("/api/opportunities/score-all")
    assert score_all.status_code == 200
    bulk = score_all.json()
    assert bulk["count"] >= 1


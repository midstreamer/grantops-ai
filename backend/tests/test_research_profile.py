def test_get_research_profile_seeded(client) -> None:
    response = client.get("/api/research-profile")

    assert response.status_code == 200
    data = response.json()

    assert data["researcher_name"] == "Chad Alessi"
    assert isinstance(data["primary_research_focus"], str)
    assert data["primary_research_focus"].strip() != ""


def test_update_research_profile(client) -> None:
    profile_response = client.get("/api/research-profile")
    assert profile_response.status_code == 200
    profile_id = profile_response.json()["id"]

    update_response = client.put(
        f"/api/research-profile/{profile_id}",
        json={"primary_research_focus": "New primary focus"},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["primary_research_focus"] == "New primary focus"


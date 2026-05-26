from unittest.mock import patch

MOCK_WORK = {
    "id": "https://openalex.org/W1234567890",
    "title": "Human-AI Teaming in Cybersecurity",
    "publication_year": 2024,
    "doi": "https://doi.org/10.1000/example",
    "cited_by_count": 42,
    "authorships": [
        {
            "author": {"display_name": "Jane Doe"},
        }
    ],
    "primary_location": {
        "landing_page_url": "https://example.com/paper",
        "source": {"display_name": "Journal of Cyber Research"},
    },
    "abstract_inverted_index": {"Human": [0], "AI": [1], "security": [2]},
}


@patch("app.services.openalex_service.search_works")
def test_opportunity_literature_search(mock_search, client) -> None:
    mock_search.return_value = [MOCK_WORK]

    opp = client.post(
        "/api/opportunities",
        json={
            "source": "manual",
            "title": "Cybersecurity AI workforce grant",
            "agency": "NSF",
            "raw_data": {
                "fit_analysis": {
                    "matched_keywords": ["human-AI teaming", "decision support"],
                }
            },
        },
    )
    assert opp.status_code == 201
    opp_id = opp.json()["id"]

    found = client.post(f"/api/opportunities/{opp_id}/literature")
    assert found.status_code == 200
    items = found.json()
    assert len(items) >= 1
    assert items[0]["source"] == "openalex"
    assert items[0]["source_id"] == "W1234567890"
    assert items[0]["title"] == "Human-AI Teaming in Cybersecurity"

    listed = client.get(f"/api/opportunities/{opp_id}/literature")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


@patch("app.services.openalex_service.search_works")
def test_literature_search_endpoint(mock_search, client) -> None:
    mock_search.return_value = [MOCK_WORK]

    response = client.post(
        "/api/literature/search",
        json={"query": "human AI teaming cybersecurity", "per_page": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["authors"] == ["Jane Doe"]

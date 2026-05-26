from unittest.mock import patch

from app.agents.base_agent import AgentStepResult
from app.agents.grantops_orchestrator import DiscoveryWorkflowReport, GrantOpsOrchestrator


def test_discovery_workflow_endpoint(client) -> None:
    with patch.object(GrantOpsOrchestrator, "run_discovery_workflow") as mock_run:
        mock_run.return_value = DiscoveryWorkflowReport(
            query="cybersecurity workforce",
            rows=25,
            status="completed",
            steps=[
                AgentStepResult(
                    step="research_profile",
                    status="completed",
                    message="Loaded profile",
                    data={"profile_id": 1},
                )
            ],
            profile={"profile_id": 1},
            opportunities_saved=3,
            opportunities_scored=3,
            top_opportunities=[{"id": 1, "title": "Test Grant", "fit_score": 80}],
        )

        response = client.post(
            "/api/agents/discovery-workflow",
            json={
                "query": "cybersecurity workforce human AI decision support",
                "rows": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["opportunities_saved"] == 3
    assert len(body["steps"]) == 1


def test_orchestrator_stops_when_profile_missing(client) -> None:
    from app.db.seed import ensure_default_research_profile
    from app.db.session import SessionLocal
    from app.models.research_profile import ResearchProfile

    db = SessionLocal()
    try:
        profiles = db.query(ResearchProfile).all()
        for profile in profiles:
            db.delete(profile)
        db.commit()

        orchestrator = GrantOpsOrchestrator(db)
        report = orchestrator.run_discovery_workflow(
            query="cybersecurity workforce",
            rows=5,
        )
        assert report.status == "failed"
        assert report.steps[0].step == "research_profile"
        assert report.steps[0].status == "failed"

        ensure_default_research_profile(db)
        db.commit()
    finally:
        db.close()


def test_orchestrator_discovery_workflow_with_mocks(client) -> None:
    from app.db.seed import ensure_default_research_profile
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        ensure_default_research_profile(db)
        db.commit()

        orchestrator = GrantOpsOrchestrator(db)

        with (
            patch(
                "app.agents.funding_discovery_agent.search_and_persist_grants_gov",
            ) as mock_search,
            patch(
                "app.agents.literature_agent.search_and_persist",
                return_value=[],
            ),
            patch(
                "app.agents.proposal_agent.summarize_opportunity",
                return_value={
                    "opportunity_summary": "Summary",
                    "why_it_fits": "Fit",
                    "concerns": "None",
                    "recommended_framing": "Frame",
                    "recommended_next_actions": "Next",
                    "possible_proposal_title": "Title",
                },
            ),
        ):
            from app.models.grant_opportunity import GrantOpportunity

            def _fake_search(session, **kwargs):
                opp = GrantOpportunity(
                    source="grants.gov",
                    source_id="workflow-test-1",
                    title="Workflow Test Grant",
                    agency="NSF",
                    recommendation="unreviewed",
                    status="new",
                )
                session.add(opp)
                session.commit()
                session.refresh(opp)
                return [opp]

            mock_search.side_effect = _fake_search

            report = orchestrator.run_discovery_workflow(
                query="cybersecurity workforce",
                rows=5,
            )

        assert report.status in {"completed", "completed_with_errors"}
        step_names = [step.step for step in report.steps]
        assert "research_profile" in step_names
        assert "funding_discovery" in step_names
        assert "fit_scoring" in step_names
        assert "select_top_opportunities" in step_names
    finally:
        db.close()

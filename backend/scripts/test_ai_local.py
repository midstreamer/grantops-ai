from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.llm_service import concept_note_markdown_has_required_sections

BASE_URL = "http://localhost:8000"
DEFAULT_PROMPT = (
    "Write one sentence explaining why human-AI teaming matters in "
    "cybersecurity operations."
)


def log_result(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")


def ensure_research_profile(client: httpx.Client) -> Optional[int]:
    response = client.get(f"{BASE_URL}/api/research-profile")
    if response.status_code == 200:
        return response.json().get("id")
    return None


def ensure_test_opportunity(client: httpx.Client) -> Optional[int]:
    list_resp = client.get(f"{BASE_URL}/api/opportunities")
    if list_resp.status_code == 200:
        for opp in list_resp.json():
            if opp.get("title") == "Human-Centered AI for Cybersecurity Workforce Development":
                return opp.get("id")

    payload = {
        "source": "manual",
        "title": "Human-Centered AI for Cybersecurity Workforce Development",
        "agency": "NSF",
        "description": (
            "This opportunity supports research on human-centered artificial intelligence, "
            "cybersecurity education, workforce development, simulation-based learning, "
            "trustworthy AI, and decision support systems."
        ),
        "deadline": "2026-09-15",
        "status": "new",
    }
    created = client.post(f"{BASE_URL}/api/opportunities", json=payload)
    if created.status_code in (200, 201):
        return created.json().get("id")
    return None


def main() -> int:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")

    with httpx.Client(timeout=60) as client:
        # 1) AI health
        health = client.get(f"{BASE_URL}/api/ai/health")
        if health.status_code != 200:
            log_result("AI health endpoint", False, f"HTTP {health.status_code}")
            return 1
        health_body = health.json()
        log_result(
            "AI health endpoint",
            True,
            f"provider={health_body.get('llm_provider')} available={health_body.get('ai_features_available')}",
        )

        # 2) AI smoke test
        smoke = client.post(
            f"{BASE_URL}/api/ai/smoke-test",
            json={"prompt": os.getenv("AI_SMOKE_PROMPT", DEFAULT_PROMPT)},
        )
        if smoke.status_code != 200:
            log_result("AI smoke test endpoint", False, f"HTTP {smoke.status_code}")
            return 1
        smoke_body = smoke.json()
        log_result(
            "AI smoke test endpoint",
            bool(smoke_body.get("success")),
            smoke_body.get("response", "")[:160],
        )

        # 3) ensure profile
        profile_id = ensure_research_profile(client)
        log_result("Ensure research profile", profile_id is not None, f"id={profile_id}")
        if profile_id is None:
            return 1

        # 4) ensure opportunity
        opportunity_id = ensure_test_opportunity(client)
        log_result("Ensure test opportunity", opportunity_id is not None, f"id={opportunity_id}")
        if opportunity_id is None:
            return 1

        # 5) AI summary
        summary_resp = client.post(f"{BASE_URL}/api/opportunities/{opportunity_id}/ai-summary")
        summary_ok = summary_resp.status_code == 200
        log_result(
            "Generate AI opportunity summary",
            summary_ok,
            f"HTTP {summary_resp.status_code}",
        )
        if summary_ok:
            summary = summary_resp.json()
            log_result(
                "AI summary content check",
                bool(summary.get("opportunity_summary")),
                summary.get("opportunity_summary", "")[:160],
            )

        # 6) concept note
        concept_resp = client.post(f"{BASE_URL}/api/opportunities/{opportunity_id}/concept-note")
        concept_ok = concept_resp.status_code in (200, 201)
        log_result(
            "Generate concept note",
            concept_ok,
            f"HTTP {concept_resp.status_code}",
        )
        if concept_ok:
            draft = concept_resp.json()
            has_sections = concept_note_markdown_has_required_sections(
                draft.get("content", ""),
                title=draft.get("title", ""),
            )
            log_result("Concept note sections check", has_sections)

        # 7) discovery workflow
        workflow = client.post(
            f"{BASE_URL}/api/agents/discovery-workflow",
            json={"query": "human AI cybersecurity workforce", "rows": 10},
        )
        workflow_ok = workflow.status_code == 200
        log_result(
            "Agent discovery workflow",
            workflow_ok,
            f"HTTP {workflow.status_code}",
        )
        if workflow_ok:
            body = workflow.json()
            log_result(
                "Workflow report steps",
                isinstance(body.get("steps"), list) and len(body.get("steps")) > 0,
                f"status={body.get('status')}",
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

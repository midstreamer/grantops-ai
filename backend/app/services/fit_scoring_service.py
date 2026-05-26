from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.models.grant_opportunity import GrantOpportunity
from app.models.research_profile import ResearchProfile


@dataclass(frozen=True)
class ScoreBreakdown:
    topic_alignment: int
    method_alignment: int
    funder_relevance: int
    eligibility_fit: int
    deadline_feasibility: int
    budget_fit: int
    collaboration_potential: int
    academic_career_value: int

    @property
    def total(self) -> int:
        return (
            self.topic_alignment
            + self.method_alignment
            + self.funder_relevance
            + self.eligibility_fit
            + self.deadline_feasibility
            + self.budget_fit
            + self.collaboration_potential
            + self.academic_career_value
        )


def _norm(text: Optional[str]) -> str:
    return (text or "").strip().lower()


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _count_matches(text: str, terms: list[str]) -> list[str]:
    seen: list[str] = []
    for term in terms:
        t = _norm(term)
        if t and t in text and t not in seen:
            seen.append(t)
    return seen


def _deadline_score(deadline: Optional[date]) -> tuple[int, list[str]]:
    concerns: list[str] = []
    if deadline is None:
        concerns.append("Deadline missing; planning certainty is limited.")
        return 5, concerns

    today = date.today()
    days = (deadline - today).days
    if days > 90:
        return 10, concerns
    if 30 <= days <= 90:
        concerns.append("Deadline is within 90 days; timeline may be compressed.")
        return 7, concerns
    if 0 <= days < 30:
        concerns.append("Deadline is within 30 days; execution risk is high.")
        return 3, concerns
    concerns.append("Deadline has already passed.")
    return 0, concerns


def _recommendation(score: int) -> str:
    if score >= 75:
        return "pursue"
    if score >= 50:
        return "monitor"
    return "decline"


def score_opportunity(opportunity: GrantOpportunity, profile: ResearchProfile) -> dict:
    """
    Rules-based fit scoring (100 points total) for an opportunity/profile pair.
    """
    title = _norm(opportunity.title)
    description = _norm(opportunity.description)
    body_text = f"{title} {description}".strip()
    agency = _norm(opportunity.agency)
    eligibility_text = _norm(opportunity.eligibility)

    profile_keywords = [*profile.keywords, *profile.research_domains]
    matched_keywords = _count_matches(body_text, profile_keywords)

    # 1) Topic alignment (30)
    keyword_pool = [k for k in profile_keywords if _norm(k)]
    max_topic_refs = max(1, min(len(keyword_pool), 12))
    topic_ratio = min(1.0, len(matched_keywords) / max_topic_refs)
    topic_alignment = round(30 * topic_ratio)

    # 2) Method alignment (15)
    method_terms = [
        "experiment",
        "simulation",
        "training",
        "workforce",
        "evaluation",
        "measurement",
        "human factors",
        "ai",
        "decision support",
    ]
    profile_method_terms = [*_count_matches(_norm(" ".join(profile.methods)), method_terms)]
    opportunity_method_matches = _count_matches(body_text, method_terms)
    method_matches = list(dict.fromkeys([*profile_method_terms, *opportunity_method_matches]))
    method_alignment = round(15 * min(1.0, len(method_matches) / len(method_terms)))

    # 3) Funder relevance (10)
    priority_funders = ["nsf", "nist", "dhs", "dod", "doe"]
    if _contains_any(agency, priority_funders):
        funder_relevance = 10
    elif _contains_any(agency, ["foundation", "institute", "department"]):
        funder_relevance = 6
    elif agency:
        funder_relevance = 4
    else:
        funder_relevance = 2

    # 4) Eligibility fit (15)
    academic_terms = [
        "university",
        "college",
        "higher education",
        "nonprofit",
        "academic",
        "research institution",
    ]
    exclusion_terms = ["individual", "for-profit only", "non-u.s.", "ineligible"]
    if not eligibility_text:
        eligibility_fit = 8
    elif _contains_any(eligibility_text, exclusion_terms):
        eligibility_fit = 3
    elif _contains_any(eligibility_text, academic_terms):
        eligibility_fit = 15
    else:
        eligibility_fit = 10

    # 5) Deadline feasibility (10)
    deadline_feasibility, deadline_concerns = _deadline_score(opportunity.deadline)

    # 6) Budget fit (5)
    budget_fit = 3
    if opportunity.award_ceiling is not None:
        if opportunity.award_ceiling >= 300000:
            budget_fit = 5
        elif opportunity.award_ceiling >= 100000:
            budget_fit = 4
        else:
            budget_fit = 2

    # 7) Collaboration potential (10)
    collaboration_terms = [
        "partnership",
        "consortium",
        "collaboration",
        "multi-institution",
        "cross-disciplinary",
        "team",
    ]
    collab_hits = _count_matches(body_text, collaboration_terms)
    collaboration_potential = round(10 * min(1.0, len(collab_hits) / 3))

    # 8) Academic career value (5)
    career_terms = ["education", "training", "workforce", "scholarship", "capacity building"]
    career_hits = _count_matches(body_text, career_terms)
    academic_career_value = round(5 * min(1.0, len(career_hits) / 2))

    breakdown = ScoreBreakdown(
        topic_alignment=topic_alignment,
        method_alignment=method_alignment,
        funder_relevance=funder_relevance,
        eligibility_fit=eligibility_fit,
        deadline_feasibility=deadline_feasibility,
        budget_fit=budget_fit,
        collaboration_potential=collaboration_potential,
        academic_career_value=academic_career_value,
    )
    fit_score = max(0, min(100, int(round(breakdown.total))))
    recommendation = _recommendation(fit_score)

    concerns: list[str] = [*deadline_concerns]
    if topic_alignment < 15:
        concerns.append("Low topical overlap with profile domains and keywords.")
    if method_alignment < 8:
        concerns.append("Method alignment appears weak for current profile methods.")
    if funder_relevance < 6:
        concerns.append("Funder is not in the highest-priority target list.")
    if eligibility_fit <= 5:
        concerns.append("Eligibility language may limit applicant fit.")

    if recommendation == "pursue":
        next_action = "Schedule go/no-go review and outline concept paper."
    elif recommendation == "monitor":
        next_action = "Track updates and gather missing details before committing."
    else:
        next_action = "Deprioritize for now and revisit only if profile changes."

    fit_summary = (
        f"Fit score {fit_score}/100 with strong signals in topic ({topic_alignment}/30), "
        f"method ({method_alignment}/15), and funder relevance ({funder_relevance}/10)."
    )

    return {
        "fit_score": fit_score,
        "recommendation": recommendation,
        "fit_summary": fit_summary,
        "matched_keywords": matched_keywords,
        "concerns": concerns,
        "recommended_next_action": next_action,
        "breakdown": {
            "topic_alignment": topic_alignment,
            "method_alignment": method_alignment,
            "funder_relevance": funder_relevance,
            "eligibility_fit": eligibility_fit,
            "deadline_feasibility": deadline_feasibility,
            "budget_fit": budget_fit,
            "collaboration_potential": collaboration_potential,
            "academic_career_value": academic_career_value,
        },
    }


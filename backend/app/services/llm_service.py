from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.models.grant_opportunity import GrantOpportunity
from app.models.literature_item import LiteratureItem
from app.models.research_profile import ResearchProfile

logger = logging.getLogger(__name__)


class LLMNotConfiguredError(Exception):
    """Raised when LLM_PROVIDER or the required API key is missing."""


class LLMProviderError(Exception):
    """Raised when an LLM API call fails."""


class LLMProvider(ABC):
    @abstractmethod
    def summarize_opportunity(
        self,
        opportunity: GrantOpportunity,
        profile: ResearchProfile,
        literature_items: list[LiteratureItem],
    ) -> dict[str, str]:
        """Return structured AI summary fields for an opportunity."""

    @abstractmethod
    def draft_concept_note(
        self,
        opportunity: GrantOpportunity,
        profile: ResearchProfile,
        literature_items: list[LiteratureItem],
    ) -> str:
        """Return a draft concept note as plain text / markdown."""

    @abstractmethod
    def draft_concept_note_structured(
        self,
        opportunity: GrantOpportunity,
        profile: ResearchProfile,
        literature_items: list[LiteratureItem],
    ) -> dict[str, str]:
        """Return structured concept note sections."""


def _format_date(value: Any) -> str:
    if value is None:
        return "N/A"
    return str(value)


def _build_context(
    opportunity: GrantOpportunity,
    profile: ResearchProfile,
    literature_items: list[LiteratureItem],
) -> str:
    raw = opportunity.raw_data if isinstance(opportunity.raw_data, dict) else {}
    fit_analysis = raw.get("fit_analysis") if isinstance(raw.get("fit_analysis"), dict) else {}

    literature_lines = []
    for item in literature_items[:10]:
        authors = ", ".join(item.authors[:3]) if item.authors else "Unknown"
        literature_lines.append(
            f"- {item.title} ({item.publication_year or 'n.d.'}); {authors}; "
            f"cited_by={item.cited_by_count or 0}"
        )

    return f"""
RESEARCH PROFILE
- Researcher: {profile.researcher_name}
- Institution: {profile.institution or 'N/A'}
- Primary focus: {profile.primary_research_focus}
- Domains: {', '.join(profile.research_domains or [])}
- Methods: {', '.join(profile.methods or [])}
- Target funders: {', '.join(profile.target_funders or [])}
- Keywords: {', '.join(profile.keywords or [])}

GRANT OPPORTUNITY
- Title: {opportunity.title}
- Agency: {opportunity.agency or 'N/A'}
- Program: {opportunity.program or 'N/A'}
- Source: {opportunity.source} ({opportunity.source_id or 'no id'})
- Deadline: {_format_date(opportunity.deadline)}
- Posted: {_format_date(opportunity.posted_date)}
- Award range: {opportunity.award_floor or '?'} – {opportunity.award_ceiling or '?'}
- Fit score: {opportunity.fit_score if opportunity.fit_score is not None else 'not scored'}
- Recommendation: {opportunity.recommendation}
- Status: {opportunity.status}
- Description: {opportunity.description or 'N/A'}
- Eligibility: {opportunity.eligibility or 'N/A'}
- Fit summary: {opportunity.fit_summary or 'N/A'}
- Fit concerns: {', '.join(fit_analysis.get('concerns') or []) or 'N/A'}
- Matched keywords: {', '.join(fit_analysis.get('matched_keywords') or []) or 'N/A'}

SUPPORTING LITERATURE ({len(literature_items)} items)
{chr(10).join(literature_lines) if literature_lines else '- None saved yet'}
""".strip()


SUMMARY_JSON_SCHEMA = """
Return a single JSON object with exactly these string keys:
{
  "opportunity_summary": "Plain-English summary of the grant opportunity (2-4 sentences).",
  "why_it_fits": "Why this opportunity aligns with the research profile.",
  "concerns": "Risks, gaps, or misalignments to watch.",
  "recommended_framing": "How to position the proposal narrative.",
  "recommended_next_actions": "Concrete next steps for the PI team.",
  "possible_proposal_title": "A compelling working title for a proposal."
}
""".strip()

CONCEPT_NOTE_JSON_SCHEMA = """
Return a single JSON object with exactly these string keys (use markdown within values where helpful):
{
  "working_title": "Compelling working title for the proposal.",
  "problem_statement": "Clear problem statement.",
  "research_gap": "What is missing in current knowledge or practice.",
  "proposed_study": "Overview of the proposed study.",
  "research_questions": "Numbered or bulleted research questions.",
  "methods": "Methods and study design.",
  "expected_contributions": "Scientific and practical contributions.",
  "broader_impacts": "Broader impacts for society, workforce, or security.",
  "why_this_funder_should_care": "Alignment with funder priorities.",
  "immediate_next_steps": "Concrete immediate next steps for the team."
}
""".strip()

CONCEPT_NOTE_SECTIONS = [
    ("working_title", "Working Title"),
    ("problem_statement", "Problem Statement"),
    ("research_gap", "Research Gap"),
    ("proposed_study", "Proposed Study"),
    ("research_questions", "Research Questions"),
    ("methods", "Methods"),
    ("expected_contributions", "Expected Contributions"),
    ("broader_impacts", "Broader Impacts"),
    ("why_this_funder_should_care", "Why This Funder Should Care"),
    ("immediate_next_steps", "Immediate Next Steps"),
]


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMProviderError("LLM returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise LLMProviderError("LLM JSON response must be an object.")
    return data


def _normalize_concept_note(data: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, _label in CONCEPT_NOTE_SECTIONS:
        value = data.get(key, "")
        result[key] = str(value).strip() if value is not None else ""
    return result


def concept_note_to_markdown(data: dict[str, str]) -> str:
    parts: list[str] = []
    for key, label in CONCEPT_NOTE_SECTIONS:
        body = data.get(key, "").strip()
        if not body:
            continue
        if key == "working_title":
            parts.append(f"# {body}\n")
        else:
            parts.append(f"## {label}\n\n{body}\n")
    return "\n".join(parts).strip()


def _normalize_summary(data: dict[str, Any]) -> dict[str, str]:
    required_keys = [
        "opportunity_summary",
        "why_it_fits",
        "concerns",
        "recommended_framing",
        "recommended_next_actions",
        "possible_proposal_title",
    ]
    result: dict[str, str] = {}
    for key in required_keys:
        value = data.get(key, "")
        result[key] = str(value).strip() if value is not None else ""
    return result


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model

    def _chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.4,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=90) as client:
                response = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            logger.exception("OpenAI API HTTP error")
            raise LLMProviderError("OpenAI API request failed.") from exc

        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Unexpected OpenAI response shape.") from exc

    def summarize_opportunity(
        self,
        opportunity: GrantOpportunity,
        profile: ResearchProfile,
        literature_items: list[LiteratureItem],
    ) -> dict[str, str]:
        context = _build_context(opportunity, profile, literature_items)
        system = (
            "You are a grant strategist helping a university researcher evaluate funding "
            "opportunities. Be specific, practical, and honest."
        )
        user = f"{context}\n\n{SUMMARY_JSON_SCHEMA}"
        content = self._chat(system, user, json_mode=True)
        return _normalize_summary(_parse_json_response(content))

    def draft_concept_note(
        self,
        opportunity: GrantOpportunity,
        profile: ResearchProfile,
        literature_items: list[LiteratureItem],
    ) -> str:
        structured = self.draft_concept_note_structured(
            opportunity, profile, literature_items
        )
        return concept_note_to_markdown(structured)

    def draft_concept_note_structured(
        self,
        opportunity: GrantOpportunity,
        profile: ResearchProfile,
        literature_items: list[LiteratureItem],
    ) -> dict[str, str]:
        context = _build_context(opportunity, profile, literature_items)
        system = (
            "You are an expert grant writer preparing a concept note for a federal or "
            "foundation grant. Be specific, credible, and aligned with the researcher profile."
        )
        user = f"{context}\n\n{CONCEPT_NOTE_JSON_SCHEMA}"
        content = self._chat(system, user, json_mode=True)
        return _normalize_concept_note(_parse_json_response(content))


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key
        self.model = model

    def _generate(self, prompt: str, *, json_mode: bool = False) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        generation_config: dict[str, Any] = {"temperature": 0.4}
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }

        try:
            with httpx.Client(timeout=90) as client:
                response = client.post(
                    url,
                    params={"key": self.api_key},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            logger.exception("Gemini API HTTP error")
            raise LLMProviderError("Gemini API request failed.") from exc

        try:
            return body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Unexpected Gemini response shape.") from exc

    def summarize_opportunity(
        self,
        opportunity: GrantOpportunity,
        profile: ResearchProfile,
        literature_items: list[LiteratureItem],
    ) -> dict[str, str]:
        context = _build_context(opportunity, profile, literature_items)
        prompt = (
            "You are a grant strategist helping a university researcher evaluate funding "
            "opportunities. Be specific, practical, and honest.\n\n"
            f"{context}\n\n{SUMMARY_JSON_SCHEMA}"
        )
        content = self._generate(prompt, json_mode=True)
        return _normalize_summary(_parse_json_response(content))

    def draft_concept_note(
        self,
        opportunity: GrantOpportunity,
        profile: ResearchProfile,
        literature_items: list[LiteratureItem],
    ) -> str:
        structured = self.draft_concept_note_structured(
            opportunity, profile, literature_items
        )
        return concept_note_to_markdown(structured)

    def draft_concept_note_structured(
        self,
        opportunity: GrantOpportunity,
        profile: ResearchProfile,
        literature_items: list[LiteratureItem],
    ) -> dict[str, str]:
        context = _build_context(opportunity, profile, literature_items)
        prompt = (
            "You are an expert grant writer preparing a concept note for a federal or "
            "foundation grant. Be specific, credible, and aligned with the researcher profile.\n\n"
            f"{context}\n\n{CONCEPT_NOTE_JSON_SCHEMA}"
        )
        content = self._generate(prompt, json_mode=True)
        return _normalize_concept_note(_parse_json_response(content))


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = (settings.llm_provider or "").strip().lower()

    if not provider:
        raise LLMNotConfiguredError(
            "LLM is not configured. Set LLM_PROVIDER to 'openai' or 'gemini' in your .env file."
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise LLMNotConfiguredError(
                "OpenAI is selected but OPENAI_API_KEY is not set. Add OPENAI_API_KEY to your .env file."
            )
        return OpenAIProvider(settings.openai_api_key)

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMNotConfiguredError(
                "Gemini is selected but GEMINI_API_KEY is not set. Add GEMINI_API_KEY to your .env file."
            )
        return GeminiProvider(settings.gemini_api_key)

    raise LLMNotConfiguredError(
        f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. Use 'openai' or 'gemini'."
    )


def summarize_opportunity(
    opportunity: GrantOpportunity,
    profile: ResearchProfile,
    literature_items: list[LiteratureItem],
) -> dict[str, str]:
    return get_llm_provider().summarize_opportunity(opportunity, profile, literature_items)


def draft_concept_note(
    opportunity: GrantOpportunity,
    profile: ResearchProfile,
    literature_items: list[LiteratureItem],
) -> str:
    return get_llm_provider().draft_concept_note(opportunity, profile, literature_items)


def draft_concept_note_structured(
    opportunity: GrantOpportunity,
    profile: ResearchProfile,
    literature_items: list[LiteratureItem],
) -> dict[str, str]:
    return get_llm_provider().draft_concept_note_structured(
        opportunity, profile, literature_items
    )

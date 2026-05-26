from __future__ import annotations

import logging
import re
from typing import Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.grant_opportunity import GrantOpportunity
from app.models.literature_item import LiteratureItem
from app.models.research_profile import ResearchProfile

logger = logging.getLogger(__name__)

OPENALEX_WORKS_URL = "https://api.openalex.org/works"
SOURCE_NAME = "openalex"


def _abstract_from_inverted_index(index: Optional[dict[str, list[int]]]) -> Optional[str]:
    if not index:
        return None
    parts: list[tuple[int, str]] = []
    for word, positions in index.items():
        for pos in positions:
            parts.append((pos, word))
    if not parts:
        return None
    parts.sort(key=lambda item: item[0])
    return " ".join(word for _, word in parts)


def _extract_openalex_id(work_id: Any) -> str:
    if not work_id:
        return ""
    value = str(work_id)
    match = re.search(r"(W\d+)", value)
    return match.group(1) if match else value.rsplit("/", 1)[-1]


def _extract_authors(work: dict[str, Any]) -> list[str]:
    authors: list[str] = []
    for authorship in work.get("authorships") or []:
        if not isinstance(authorship, dict):
            continue
        author = authorship.get("author") or {}
        name = author.get("display_name") if isinstance(author, dict) else None
        if not name:
            name = authorship.get("raw_author_name")
        if name and name not in authors:
            authors.append(str(name))
    return authors


def _extract_venue(work: dict[str, Any]) -> Optional[str]:
    primary = work.get("primary_location")
    if isinstance(primary, dict):
        source = primary.get("source")
        if isinstance(source, dict) and source.get("display_name"):
            return str(source["display_name"])
        if primary.get("raw_source_name"):
            return str(primary["raw_source_name"])
    host = work.get("host_venue")
    if isinstance(host, dict) and host.get("display_name"):
        return str(host["display_name"])
    return None


def _extract_url(work: dict[str, Any]) -> Optional[str]:
    primary = work.get("primary_location")
    if isinstance(primary, dict):
        for key in ("landing_page_url", "pdf_url"):
            if primary.get(key):
                return str(primary[key])
    if work.get("doi"):
        return str(work["doi"])
    if work.get("id"):
        return str(work["id"])
    return None


def _normalize_doi(doi: Any) -> Optional[str]:
    if not doi:
        return None
    value = str(doi).strip()
    return value.replace("https://doi.org/", "").replace("http://doi.org/", "")


def normalize_work(work: dict[str, Any]) -> dict[str, Any]:
    """Normalize an OpenAlex work object into LiteratureItem field values."""
    source_id = _extract_openalex_id(work.get("id"))
    abstract = work.get("abstract")
    if not abstract and work.get("abstract_inverted_index"):
        abstract = _abstract_from_inverted_index(work.get("abstract_inverted_index"))

    return {
        "source": SOURCE_NAME,
        "source_id": source_id,
        "title": str(work.get("title") or work.get("display_name") or "Untitled"),
        "authors": _extract_authors(work),
        "publication_year": work.get("publication_year"),
        "venue": _extract_venue(work),
        "doi": _normalize_doi(work.get("doi")),
        "url": _extract_url(work),
        "abstract": str(abstract) if abstract else None,
        "cited_by_count": work.get("cited_by_count"),
        "raw_data": work,
    }


def search_works(query: str, per_page: int = 10) -> list[dict[str, Any]]:
    """Query OpenAlex works API and return raw work objects."""
    settings = get_settings()
    params: dict[str, Any] = {
        "search": query.strip(),
        "per_page": min(max(per_page, 1), 100),
    }
    if getattr(settings, "openalex_api_key", None):
        params["api_key"] = settings.openalex_api_key

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(OPENALEX_WORKS_URL, params=params)
            response.raise_for_status()
            body = response.json()
    except httpx.HTTPError as exc:
        logger.exception("OpenAlex search HTTP error", extra={"query": query})
        raise RuntimeError("OpenAlex literature search failed") from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("OpenAlex search unexpected error", extra={"query": query})
        raise RuntimeError("OpenAlex literature search failed") from exc

    results = body.get("results") if isinstance(body, dict) else None
    if not isinstance(results, list):
        logger.error("OpenAlex unexpected response shape", extra={"body_type": type(body)})
        return []

    return [work for work in results if isinstance(work, dict)]


def build_opportunity_literature_query(
    opportunity: GrantOpportunity,
    profile: ResearchProfile,
) -> str:
    """Build a search query from opportunity title, matched keywords, and profile keywords."""
    terms: list[str] = []

    if opportunity.title:
        terms.append(opportunity.title.strip())

    raw = opportunity.raw_data if isinstance(opportunity.raw_data, dict) else {}
    fit_analysis = raw.get("fit_analysis")
    if isinstance(fit_analysis, dict):
        matched = fit_analysis.get("matched_keywords")
        if isinstance(matched, list):
            terms.extend(str(k).strip() for k in matched if k)

    for keyword in (profile.keywords or [])[:8]:
        if keyword:
            terms.append(str(keyword).strip())

    for domain in (profile.research_domains or [])[:5]:
        if domain:
            terms.append(str(domain).strip())

    # De-duplicate while preserving order; cap length for OpenAlex URL limits.
    seen: set[str] = set()
    unique_terms: list[str] = []
    for term in terms:
        key = term.lower()
        if key and key not in seen:
            seen.add(key)
            unique_terms.append(term)

    if not unique_terms:
        return opportunity.title or profile.primary_research_focus

    query = " ".join(unique_terms[:12])
    return query[:500]


def upsert_literature_item(
    db: Session,
    normalized: dict[str, Any],
    *,
    opportunity_id: Optional[int] = None,
) -> LiteratureItem:
    stmt = select(LiteratureItem).where(
        LiteratureItem.source == normalized["source"],
        LiteratureItem.source_id == normalized["source_id"],
        LiteratureItem.opportunity_id == opportunity_id,
    )
    existing = db.execute(stmt).scalars().first()

    if existing is None:
        item = LiteratureItem(
            opportunity_id=opportunity_id,
            **normalized,
        )
        db.add(item)
        return item

    existing.title = normalized["title"]
    existing.authors = normalized["authors"]
    existing.publication_year = normalized.get("publication_year")
    existing.venue = normalized.get("venue")
    existing.doi = normalized.get("doi")
    existing.url = normalized.get("url")
    existing.abstract = normalized.get("abstract")
    existing.cited_by_count = normalized.get("cited_by_count")
    existing.raw_data = normalized.get("raw_data") or {}
    db.add(existing)
    return existing


def search_and_persist(
    db: Session,
    *,
    query: str,
    per_page: int = 10,
    opportunity_id: Optional[int] = None,
) -> list[LiteratureItem]:
    works = search_works(query, per_page=per_page)
    saved: list[LiteratureItem] = []

    for work in works:
        normalized = normalize_work(work)
        if not normalized["source_id"]:
            continue
        item = upsert_literature_item(db, normalized, opportunity_id=opportunity_id)
        saved.append(item)

    db.commit()
    for item in saved:
        db.refresh(item)

    return saved

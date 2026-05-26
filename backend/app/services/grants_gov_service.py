from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.grant_opportunity import GrantOpportunity

logger = logging.getLogger(__name__)


GRANTS_GOV_BASE_URL = "https://api.grants.gov/v1/api"


@dataclass(frozen=True)
class GrantsGovSearchResult:
    """Normalized shape used by this service before persistence."""

    source_id: str
    title: str
    agency: Optional[str]
    posted_date: Optional[date]
    deadline: Optional[date]
    opportunity_status: Optional[str]
    raw_data: dict[str, Any]


def _parse_mmddyyyy(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        for fmt in ("%m/%d/%Y", "%m/%d/%y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        v = value.strip()
        if v == "":
            return None
        try:
            return float(v.replace(",", ""))
        except ValueError:
            return None
    return None


def search_grants_gov(query: str, rows: int = 25) -> list[dict[str, Any]]:
    """
    Call Grants.gov search2 endpoint.

    Returns the raw list under data.oppHits (shape can vary over time).
    """
    payload = {
        "keyword": query,
        "rows": rows,
        # Most relevant statuses for discovery; can be revisited later.
        "oppStatuses": "posted|forecasted",
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{GRANTS_GOV_BASE_URL}/search2", json=payload)
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as e:
        logger.exception("Grants.gov search2 HTTP error", extra={"query": query, "rows": rows})
        raise RuntimeError("Grants.gov search failed") from e
    except Exception as e:  # noqa: BLE001
        logger.exception("Grants.gov search2 unexpected error", extra={"query": query, "rows": rows})
        raise RuntimeError("Grants.gov search failed") from e

    data = body.get("data") if isinstance(body, dict) else None
    opp_hits = (data or {}).get("oppHits") if isinstance(data, dict) else None

    if not isinstance(opp_hits, list):
        logger.error(
            "Grants.gov search2 unexpected response shape",
            extra={"top_keys": list(body.keys()) if isinstance(body, dict) else type(body)},
        )
        return []

    return [hit for hit in opp_hits if isinstance(hit, dict)]


def fetch_grants_gov_opportunity(opportunity_id: str) -> dict[str, Any]:
    """Call Grants.gov fetchOpportunity endpoint and return the raw data payload."""
    try:
        opp_id_int = int(opportunity_id)
    except ValueError as e:
        raise ValueError("opportunity_id must be numeric for Grants.gov fetchOpportunity") from e

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{GRANTS_GOV_BASE_URL}/fetchOpportunity",
                json={"opportunityId": opp_id_int},
            )
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as e:
        logger.exception("Grants.gov fetchOpportunity HTTP error", extra={"opportunity_id": opportunity_id})
        raise RuntimeError("Grants.gov fetchOpportunity failed") from e
    except Exception as e:  # noqa: BLE001
        logger.exception("Grants.gov fetchOpportunity unexpected error", extra={"opportunity_id": opportunity_id})
        raise RuntimeError("Grants.gov fetchOpportunity failed") from e

    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        logger.error("Grants.gov fetchOpportunity unexpected response shape", extra={"body_type": type(body)})
        return {}
    return data


def _normalize_search_hit(hit: dict[str, Any]) -> Optional[GrantsGovSearchResult]:
    """
    Normalize a search2 oppHit dict into our internal opportunity shape.

    Current observed hit keys include:
    - id, number, title, agencyCode, agency, openDate, closeDate, oppStatus, docType, cfdaList
    """
    source_id = hit.get("id")
    title = hit.get("title")
    if not source_id or not title:
        return None

    agency = hit.get("agency") or hit.get("agencyName") or hit.get("agencyCode")
    posted_date = _parse_mmddyyyy(hit.get("openDate"))
    deadline = _parse_mmddyyyy(hit.get("closeDate"))
    opp_status = hit.get("oppStatus")

    return GrantsGovSearchResult(
        source_id=str(source_id),
        title=str(title),
        agency=str(agency) if agency else None,
        posted_date=posted_date,
        deadline=deadline,
        opportunity_status=str(opp_status) if opp_status else None,
        raw_data=hit,
    )


def _apply_detail_fields(opp: GrantOpportunity, detail: dict[str, Any]) -> None:
    synopsis = detail.get("synopsis") if isinstance(detail.get("synopsis"), dict) else {}

    opp.program = opp.program or detail.get("opportunityNumber")

    synopsis_desc = synopsis.get("synopsisDesc")
    if synopsis_desc and not opp.description:
        opp.description = str(synopsis_desc)

    elig = synopsis.get("applicantEligibilityDesc")
    if elig and not opp.eligibility:
        opp.eligibility = str(elig)

    ceiling = _coerce_float(synopsis.get("awardCeiling"))
    floor = _coerce_float(synopsis.get("awardFloor"))
    if ceiling is not None and opp.award_ceiling is None:
        opp.award_ceiling = ceiling
    if floor is not None and opp.award_floor is None:
        opp.award_floor = floor

    # Prefer responseDate (often the due date), fallback to existing deadline.
    response_date = synopsis.get("responseDateStr") or synopsis.get("responseDate")
    parsed_due = _parse_mmddyyyy(response_date)
    if parsed_due and opp.deadline is None:
        opp.deadline = parsed_due

    if opp.posted_date is None:
        posting = synopsis.get("postingDateStr") or synopsis.get("postingDate")
        opp.posted_date = _parse_mmddyyyy(posting)

    # raw_data: merge detail under a stable key
    if isinstance(opp.raw_data, dict):
        opp.raw_data = {**opp.raw_data, "fetchOpportunity": detail}
    else:
        opp.raw_data = {"fetchOpportunity": detail}


def upsert_grants_gov_opportunity_from_hit(
    db: Session,
    hit: dict[str, Any],
    *,
    fetch_detail: bool = False,
) -> Optional[GrantOpportunity]:
    normalized = _normalize_search_hit(hit)
    if normalized is None:
        return None

    stmt = select(GrantOpportunity).where(
        GrantOpportunity.source == "grants.gov",
        GrantOpportunity.source_id == normalized.source_id,
    )
    existing = db.execute(stmt).scalars().first()

    if existing is None:
        opp = GrantOpportunity(
            source="grants.gov",
            source_id=normalized.source_id,
            title=normalized.title,
            agency=normalized.agency,
            description=None,
            eligibility=None,
            award_ceiling=None,
            award_floor=None,
            deadline=normalized.deadline,
            posted_date=normalized.posted_date,
            opportunity_status=normalized.opportunity_status,
            url=None,
            raw_data=normalized.raw_data,
            fit_score=None,
            fit_summary=None,
            recommendation="unreviewed",
            status="new",
            next_action=None,
        )
        db.add(opp)
    else:
        opp = existing
        # Update core fields from the latest search snapshot.
        opp.title = normalized.title or opp.title
        opp.agency = normalized.agency or opp.agency
        opp.deadline = normalized.deadline or opp.deadline
        opp.posted_date = normalized.posted_date or opp.posted_date
        opp.opportunity_status = normalized.opportunity_status or opp.opportunity_status
        opp.raw_data = normalized.raw_data

    if fetch_detail:
        try:
            detail = fetch_grants_gov_opportunity(normalized.source_id)
            if detail:
                _apply_detail_fields(opp, detail)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to enrich Grants.gov opportunity with fetchOpportunity", extra={"id": normalized.source_id})

    return opp


def search_and_persist_grants_gov(
    db: Session,
    *,
    query: str,
    rows: int = 25,
    fetch_detail: bool = False,
) -> list[GrantOpportunity]:
    hits = search_grants_gov(query, rows=rows)
    saved: list[GrantOpportunity] = []

    for hit in hits:
        opp = upsert_grants_gov_opportunity_from_hit(db, hit, fetch_detail=fetch_detail)
        if opp is not None:
            saved.append(opp)

    db.commit()
    for opp in saved:
        db.refresh(opp)

    return saved


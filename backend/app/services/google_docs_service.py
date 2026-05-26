from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.proposal_draft import ProposalDraft

logger = logging.getLogger(__name__)

DOCS_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]


class GoogleDocsNotConfiguredError(Exception):
    """Raised when Google credentials are missing for Docs export."""


class GoogleDocsError(Exception):
    """Raised when a Google Docs API call fails."""


def _require_google_credentials_path() -> str:
    settings = get_settings()
    credentials_path = (settings.google_application_credentials or "").strip()
    if not credentials_path:
        raise GoogleDocsNotConfiguredError(
            "Google Docs export is not configured. Set GOOGLE_APPLICATION_CREDENTIALS "
            "in backend/.env to your service account JSON key path."
        )

    path = Path(credentials_path).expanduser()
    if not path.is_file():
        raise GoogleDocsNotConfiguredError(
            f"Google credentials file not found: {path}"
        )
    return str(path)


def get_docs_service(credentials_path: Optional[str] = None) -> Any:
    creds_file = credentials_path or _require_google_credentials_path()
    credentials = service_account.Credentials.from_service_account_file(
        creds_file,
        scopes=DOCS_SCOPES,
    )
    return build("docs", "v1", credentials=credentials, cache_discovery=False)


def google_doc_url_for_id(document_id: str) -> str:
    return f"https://docs.google.com/document/d/{document_id}/edit"


def _markdown_lines_to_requests(content: str, start_index: int) -> tuple[list[dict[str, Any]], int]:
    requests: list[dict[str, Any]] = []
    index = start_index
    heading_styles = {1: "HEADING_1", 2: "HEADING_2", 3: "HEADING_3"}

    for line in content.split("\n"):
        heading_match = re.match(r"^(#{1,3})\s+(.*)$", line.strip())
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip() + "\n"
            requests.append({"insertText": {"location": {"index": index}, "text": text}})
            end_index = index + len(text)
            requests.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": index, "endIndex": end_index - 1},
                        "paragraphStyle": {
                            "namedStyleType": heading_styles.get(level, "HEADING_2"),
                        },
                        "fields": "namedStyleType",
                    }
                }
            )
            index = end_index
            continue

        if not line.strip():
            text = "\n"
        else:
            text = line.rstrip() + "\n"

        requests.append({"insertText": {"location": {"index": index}, "text": text}})
        index += len(text)

    return requests, index


def _build_doc_insert_requests(title: str, content: str) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    index = 1

    title_line = f"{title.strip()}\n"
    requests.append({"insertText": {"location": {"index": index}, "text": title_line}})
    title_end = index + len(title_line)
    requests.append(
        {
            "updateParagraphStyle": {
                "range": {"startIndex": index, "endIndex": title_end - 1},
                "paragraphStyle": {"namedStyleType": "HEADING_1"},
                "fields": "namedStyleType",
            }
        }
    )
    index = title_end

    content_requests, _index = _markdown_lines_to_requests(content, index)
    requests.extend(content_requests)
    return requests


def create_google_doc_from_proposal_draft(db: Session, draft_id: int) -> ProposalDraft:
    """Create a Google Doc from a proposal draft and persist the document URL."""
    draft = db.get(ProposalDraft, draft_id)
    if draft is None:
        raise ValueError(f"Proposal draft {draft_id} not found.")

    docs_service = get_docs_service()

    try:
        created = docs_service.documents().create(
            body={"title": draft.title[:200]},
        ).execute()
    except HttpError as exc:
        raise GoogleDocsError(f"Failed to create Google Doc: {exc}") from exc

    document_id = created["documentId"]
    requests = _build_doc_insert_requests(draft.title, draft.content)

    if requests:
        try:
            docs_service.documents().batchUpdate(
                documentId=document_id,
                body={"requests": requests},
            ).execute()
        except HttpError as exc:
            raise GoogleDocsError(f"Failed to write Google Doc content: {exc}") from exc

    draft.google_doc_url = google_doc_url_for_id(document_id)
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft

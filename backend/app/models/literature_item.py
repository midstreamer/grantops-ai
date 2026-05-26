from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class LiteratureItem(Base):
    __tablename__ = "literature_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("grant_opportunities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[str] = mapped_column(String(200), nullable=False)

    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    authors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    venue: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    abstract: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    cited_by_count: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)

    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

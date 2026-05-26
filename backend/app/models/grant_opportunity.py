from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class GrantOpportunity(Base):
    __tablename__ = "grant_opportunities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    agency: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    program: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    eligibility: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    award_ceiling: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    award_floor: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    deadline: Mapped[Optional[date]] = mapped_column(Date(), nullable=True)
    posted_date: Mapped[Optional[date]] = mapped_column(Date(), nullable=True)
    opportunity_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    fit_score: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    fit_summary: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    recommendation: Mapped[str] = mapped_column(String(20), nullable=False, default="unreviewed")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new")

    next_action: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


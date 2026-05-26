from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ResearchProfile(Base):
    __tablename__ = "research_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    researcher_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    institution: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    primary_research_focus: Mapped[str] = mapped_column(Text(), nullable=False)
    research_domains: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    methods: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    target_funders: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    preferred_outputs: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False)
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

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ScheduledSearch(Base):
    __tablename__ = "scheduled_searches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    query: Mapped[str] = mapped_column(Text(), nullable=False)
    rows: Mapped[int] = mapped_column(Integer(), nullable=False, default=25)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False, default="weekly")
    active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

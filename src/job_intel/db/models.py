from __future__ import annotations

from sqlalchemy import Float, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    salary: Mapped[str] = mapped_column(Text, default="")
    posted_at: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(Text, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[str] = mapped_column(Text, server_default=text("CURRENT_TIMESTAMP"))


class MatchRunRecord(Base):
    __tablename__ = "match_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_preview: Mapped[str] = mapped_column(Text, nullable=False)
    resume_chars: Mapped[int] = mapped_column(Integer, nullable=False)
    min_score: Mapped[float] = mapped_column(Float, nullable=False)
    total_matches: Mapped[int] = mapped_column(Integer, nullable=False)
    qualified_matches: Mapped[int] = mapped_column(Integer, nullable=False)
    notified_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(Text, server_default=text("CURRENT_TIMESTAMP"))


class TelegramSentJobRecord(Base):
    __tablename__ = "telegram_sent_jobs"
    __table_args__ = (UniqueConstraint("source", "external_id", "chat_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    chat_id: Mapped[str] = mapped_column(String, nullable=False)
    first_sent_at: Mapped[str] = mapped_column(Text, server_default=text("CURRENT_TIMESTAMP"))
    last_sent_at: Mapped[str] = mapped_column(Text, server_default=text("CURRENT_TIMESTAMP"))
    send_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class JobFeedbackRecord(Base):
    __tablename__ = "job_feedback"
    __table_args__ = (UniqueConstraint("source", "external_id", "chat_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    chat_id: Mapped[str] = mapped_column(String, nullable=False)
    feedback: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[str] = mapped_column(Text, server_default=text("CURRENT_TIMESTAMP"))

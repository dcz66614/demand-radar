"""Pydantic models for Demand Radar. Unknown fields -> null, never invented."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, field_validator

DOMAINS = ("AI", "RES", "BIO", "FIN", "JOB", "UK")
PLATFORMS = ("github", "hackernews", "official", "reddit_authorized")


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def source_id_for(platform: str, external_id: str) -> str:
    return hashlib.sha256(f"{platform}:{external_id}".encode()).hexdigest()[:20]


def pain_id_for(domain: str, job: str, blocker: str) -> str:
    norm = lambda s: " ".join((s or "").strip().lower().split())
    return hashlib.sha256(f"{domain}|{norm(job)}|{norm(blocker)}".encode()).hexdigest()[:20]


class SourceItem(BaseModel):
    platform: Literal["github", "hackernews", "official", "reddit_authorized"]
    external_id: str
    url: str
    title: str | None = None
    excerpt: str
    published_at: str | None = None
    fetched_at: str
    domain: Literal["AI", "RES", "BIO", "FIN", "JOB", "UK"]
    source_type: str
    who: str | None = None
    job_to_be_done: str | None = None
    blocker: str | None = None
    current_workaround: str | None = None
    impact: str | None = None
    evidence_note: str | None = None
    review_status: str = "PENDING"

    @field_validator("url")
    @classmethod
    def _url_https(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("url must be https")
        return v

    @field_validator("excerpt")
    @classmethod
    def _excerpt_len(cls, v: str) -> str:
        if not v or len(v) > 300:
            raise ValueError("excerpt must be 1..300 chars")
        return v

    @field_validator("published_at", "fetched_at")
    @classmethod
    def _iso_time(cls, v):
        if v is None:
            return v
        datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")
        return v

    @property
    def source_id(self) -> str:
        return source_id_for(self.platform, self.external_id)

    @property
    def canonical_url(self) -> str:
        from .normalize import canonical_url

        return canonical_url(self.url)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(f"{self.url}|{self.excerpt}".encode()).hexdigest()[:20]

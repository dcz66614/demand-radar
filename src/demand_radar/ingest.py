"""JSONL validation + idempotent ingest. Invalid lines are rejected, never fixed up."""
from __future__ import annotations

import json
from pathlib import Path

from . import db as dbmod
from .models import SourceItem


def ingest_file(db_path, jsonl_path) -> int:
    inserted = 0
    with dbmod.connect(db_path) as conn:
        for line in Path(jsonl_path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = SourceItem.model_validate(json.loads(line))
            if dbmod.upsert_source_item(conn, item):
                inserted += 1
    return inserted

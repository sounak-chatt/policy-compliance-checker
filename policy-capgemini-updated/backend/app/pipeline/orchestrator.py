"""Orchestrator: chains parse -> Multi-Agent Council into a single ScanRecord."""
from __future__ import annotations

from app import config
from app.models import ScanRecord
from app.pipeline.parser import parse_document
from app.pipeline.agents import run_multi_agent_council


async def run_pipeline(filename: str, data: bytes, uploaded_by: str,
                 tenant_id: str = config.DEFAULT_TENANT) -> ScanRecord:
    text = parse_document(filename, data)
    if not text.strip():
        text = "(empty or unreadable document)"

    record = await run_multi_agent_council(filename, text, uploaded_by, tenant_id)
    import hashlib
    record.sha256_hash = hashlib.sha256(data).hexdigest()
    return record


"""SQLite persistence: immutable audit log + scan records."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import List

from app import config
from app.models import AuditEntry, ScanRecord


def _conn():
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            actor TEXT NOT NULL,
            role TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT NOT NULL,
            detail TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS scans (
            scan_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            payload TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS compliance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            policy_updates REAL NOT NULL,
            training_completion REAL NOT NULL,
            audit_findings REAL NOT NULL,
            security_violations REAL NOT NULL,
            documentation_quality REAL NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS custom_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_name TEXT NOT NULL,
            rules TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL DEFAULT '',
            tenant_id TEXT NOT NULL DEFAULT 'acmecorp')""")
            
        # Migration: check if version and updated_at exist in custom_policies
        cursor = c.execute("PRAGMA table_info(custom_policies)")
        cols = [col["name"] for col in cursor.fetchall()]
        if "version" not in cols:
            c.execute("ALTER TABLE custom_policies ADD COLUMN version INTEGER NOT NULL DEFAULT 1")
        if "updated_at" not in cols:
            c.execute("ALTER TABLE custom_policies ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
        if "tenant_id" not in cols:
            c.execute("ALTER TABLE custom_policies ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'acmecorp'")



def save_compliance_metric(date: str, policy_updates: float, training_completion: float, audit_findings: float, security_violations: float, documentation_quality: float):
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO compliance_metrics (date, policy_updates, training_completion, audit_findings, security_violations, documentation_quality) "
            "VALUES (?,?,?,?,?,?)",
            (date, policy_updates, training_completion, audit_findings, security_violations, documentation_quality)
        )


def get_compliance_history():
    with _conn() as c:
        rows = c.execute("SELECT * FROM compliance_metrics ORDER BY date ASC").fetchall()
    return [dict(r) for r in rows]


def log_audit(actor: str, role: str, action: str, target: str, detail: str = ""):
    with _conn() as c:
        c.execute(
            "INSERT INTO audit (timestamp, actor, role, action, target, detail) "
            "VALUES (?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), actor, role, action,
             target, detail),
        )


def get_audit(limit: int = 100) -> List[AuditEntry]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [AuditEntry(id=r["id"], timestamp=datetime.fromisoformat(r["timestamp"]),
                       actor=r["actor"], role=r["role"], action=r["action"],
                       target=r["target"], detail=r["detail"]) for r in rows]


def save_scan(record: ScanRecord):
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO scans (scan_id, created_at, payload) "
            "VALUES (?,?,?)",
            (record.scan_id, record.created_at.isoformat(),
             record.model_dump_json()),
        )


def get_scan(scan_id: str) -> ScanRecord | None:
    with _conn() as c:
        row = c.execute("SELECT payload FROM scans WHERE scan_id=?",
                        (scan_id,)).fetchone()
    return ScanRecord(**json.loads(row["payload"])) if row else None


def list_scans(tenant_id: str = None, limit: int = 50) -> List[ScanRecord]:
    with _conn() as c:
        if tenant_id:
            rows = c.execute(
                "SELECT payload FROM scans ORDER BY created_at DESC"
            ).fetchall()
            scans = []
            for r in rows:
                s = ScanRecord(**json.loads(r["payload"]))
                if s.tenant_id == tenant_id:
                    scans.append(s)
                    if len(scans) >= limit:
                        break
            return scans
        else:
            rows = c.execute(
                "SELECT payload FROM scans ORDER BY created_at DESC LIMIT ?",
                (limit,)).fetchall()
            return [ScanRecord(**json.loads(r["payload"])) for r in rows]


def save_custom_policy(policy_name: str, rules: list[str], tenant_id: str = "acmecorp") -> int:
    with _conn() as c:
        row = c.execute(
            "SELECT MAX(version) as max_v FROM custom_policies WHERE policy_name=? AND tenant_id=?",
            (policy_name, tenant_id)
        ).fetchone()
        next_version = (row["max_v"] or 0) + 1 if row else 1
        
        cursor = c.execute(
            "INSERT INTO custom_policies (policy_name, rules, version, updated_at, tenant_id) VALUES (?,?,?,?,?)",
            (policy_name, json.dumps(rules), next_version, datetime.now(timezone.utc).isoformat(), tenant_id),
        )
        return cursor.lastrowid


def list_custom_policies(tenant_id: str = None) -> list[dict]:
    with _conn() as c:
        if tenant_id:
            rows = c.execute(
                "SELECT * FROM custom_policies WHERE tenant_id=? ORDER BY policy_name ASC, version DESC",
                (tenant_id,)
            ).fetchall()
        else:
            rows = c.execute("SELECT * FROM custom_policies ORDER BY policy_name ASC, version DESC").fetchall()
    return [
        {
            "id": r["id"],
            "policy_name": r["policy_name"],
            "rules": json.loads(r["rules"]),
            "version": r["version"],
            "updated_at": r["updated_at"],
            "tenant_id": r["tenant_id"]
        }
        for r in rows
    ]



def delete_custom_policy(policy_id: int):
    with _conn() as c:
        c.execute("DELETE FROM custom_policies WHERE id=?", (policy_id,))


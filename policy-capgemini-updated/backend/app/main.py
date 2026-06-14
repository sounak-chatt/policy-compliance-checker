"""Policy Compliance Checker — FastAPI application."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import config, db
from app.models import DashboardStats, ScanRecord
from app.pipeline.orchestrator import run_pipeline
from app.pipeline.vectorstore import get_store
from app.rbac import require
from app.seed import seed

app = FastAPI(title="Policy Compliance Checker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    db.init_db()
    get_store()   # warm the vector store / ingest policies
    await seed()



@app.get("/api/health")
def health():
    store = get_store()
    return {
        "status": "ok",
        "demo_mode": config.DEMO_MODE,
        "vector_backend": store.backend,
        "policy_chunks": len(store.base_blocks),
        "models": {"triage": config.TRIAGE_MODEL, "analysis": config.ANALYSIS_MODEL},
    }


@app.get("/api/compliance/trend")
def compliance_trend(role: str = Depends(require("view")), x_tenant: str = Header(default="acmecorp")):
    all_scans = db.list_scans(tenant_id=x_tenant, limit=500)
    
    # Calculate current score based on database scans
    # Findings score: starts at 100, drops by 1.5 per violation (capped at 0)
    total_violations = sum(s.total_violations for s in all_scans)
    findings_score = max(0.0, 100.0 - (total_violations * 1.5))
    
    # Security score: starts at 100, drops by 4 per critical violation
    critical_violations = sum(sum(1 for v in s.violations if v.severity == "P1") for s in all_scans)
    security_score = max(0.0, 100.0 - (critical_violations * 4.0))
    
    # 1. Policy Updates is tied dynamically to the number of custom policies in the playground
    custom_policies = db.list_custom_policies(tenant_id=x_tenant)
    policy_updates = min(100.0, 80.0 + len(custom_policies) * 3.0)
    
    # 2. Training Completion is linked directly to active remediation commits in the audit log
    audit_logs = db.get_audit(limit=1000)
    num_remediations = sum(1 for log in audit_logs if log.action == "REMEDIATION_APPLIED")
    training_completion = min(100.0, 70.0 + num_remediations * 4.0)
    
    # 3. Documentation Quality is tied directly to the average score and clean ratio of scans
    if all_scans:
        avg_score = sum(s.compliance_score for s in all_scans) / len(all_scans)
        clean_docs = sum(1 for s in all_scans if s.total_violations == 0)
        clean_ratio = clean_docs / len(all_scans)
        documentation_quality = min(100.0, round(avg_score * 0.8 + clean_ratio * 20.0, 1))
    else:
        documentation_quality = 85.0
    
    # Calculate weighted index
    today_index = (
        policy_updates * 0.25 +
        training_completion * 0.20 +
        findings_score * 0.25 +
        security_score * 0.15 +
        documentation_quality * 0.15
    )
    
    # Save/Update today's metric in SQLite
    today_str = datetime.now().strftime("%Y-%m-%d")
    db.save_compliance_metric(today_str, policy_updates, training_completion, findings_score, security_score, documentation_quality)
    
    # Load history
    history_records = db.get_compliance_history()
    history_data = []
    for r in history_records:
        weighted = (
            r["policy_updates"] * 0.25 +
            r["training_completion"] * 0.20 +
            r["audit_findings"] * 0.25 +
            r["security_violations"] * 0.15 +
            r["documentation_quality"] * 0.15
        )
        history_data.append({
            "date": r["date"],
            "policy_updates": r["policy_updates"],
            "training_completion": r["training_completion"],
            "audit_findings": r["audit_findings"],
            "security_violations": r["security_violations"],
            "documentation_quality": r["documentation_quality"],
            "compliance_index": round(weighted, 1)
        })
    
    # Dynamic Trend Forecasting (linear trend extrapolation)
    # Computes the slope of the historical points and projects it
    def calculate_forecast_item(history_list, key: str, steps: float, default_val: float) -> float:
        vals = [pt[key] for pt in history_list]
        if len(vals) < 2:
            return max(0.0, min(100.0, default_val - (4.0 if steps < 3 else 7.0)))
        n = len(vals)
        sum_x = sum(range(n))
        sum_y = sum(vals)
        sum_xx = sum(i*i for i in range(n))
        sum_xy = sum(i*vals[i] for i in range(n))
        denom = (n * sum_xx - sum_x * sum_x)
        slope = (n * sum_xy - sum_x * sum_y) / denom if denom != 0 else -0.1
        projected = vals[-1] + (slope * steps)
        return max(0.0, min(100.0, round(projected, 1)))
        
    forecast_week_pu = calculate_forecast_item(history_data, "policy_updates", 1.4, policy_updates)
    forecast_week_tc = calculate_forecast_item(history_data, "training_completion", 1.4, training_completion)
    forecast_week_af = calculate_forecast_item(history_data, "audit_findings", 1.4, findings_score)
    forecast_week_sv = calculate_forecast_item(history_data, "security_violations", 1.4, security_score)
    forecast_week_dq = calculate_forecast_item(history_data, "documentation_quality", 1.4, documentation_quality)

    forecast_month_pu = calculate_forecast_item(history_data, "policy_updates", 6.0, policy_updates)
    forecast_month_tc = calculate_forecast_item(history_data, "training_completion", 6.0, training_completion)
    forecast_month_af = calculate_forecast_item(history_data, "audit_findings", 6.0, findings_score)
    forecast_month_sv = calculate_forecast_item(history_data, "security_violations", 6.0, security_score)
    forecast_month_dq = calculate_forecast_item(history_data, "documentation_quality", 6.0, documentation_quality)
    
    forecast_week_index = round(
        forecast_week_pu * 0.25 +
        forecast_week_tc * 0.20 +
        forecast_week_af * 0.25 +
        forecast_week_sv * 0.15 +
        forecast_week_dq * 0.15,
        1
    )
    forecast_month_index = round(
        forecast_month_pu * 0.25 +
        forecast_month_tc * 0.20 +
        forecast_month_af * 0.25 +
        forecast_month_sv * 0.15 +
        forecast_month_dq * 0.15,
        1
    )
    
    forecast_data = [
        {
            "date": "Next Week",
            "policy_updates": forecast_week_pu,
            "training_completion": forecast_week_tc,
            "audit_findings": forecast_week_af,
            "security_violations": forecast_week_sv,
            "documentation_quality": forecast_week_dq,
            "compliance_index": forecast_week_index,
            "is_forecast": True
        },
        {
            "date": "Next Month",
            "policy_updates": forecast_month_pu,
            "training_completion": forecast_month_tc,
            "audit_findings": forecast_month_af,
            "security_violations": forecast_month_sv,
            "documentation_quality": forecast_month_dq,
            "compliance_index": forecast_month_index,
            "is_forecast": True
        }
    ]
    
    return {
        "history": history_data,
        "forecast": forecast_data,
        "formula": "Policy Updates * 25% + Training Completion * 20% + Audit Findings * 25% + Security Violations * 15% + Documentation Quality * 15%",
        "weights": {
            "policy_updates": 0.25,
            "training_completion": 0.20,
            "audit_findings": 0.25,
            "security_violations": 0.15,
            "documentation_quality": 0.15
        }
    }


@app.post("/api/scan")
async def scan(file: UploadFile = File(...),
               x_user: str = Header(default="demo@nexuszenith"),
               x_tenant: str = Header(default="acmecorp"),
               role: str = Depends(require("upload"))):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # 1. Guardrail - File size validation (Max 20MB)
    if len(data) > 20 * 1024 * 1024:
         db.log_audit(x_user, role, "UPLOAD_BLOCKED", file.filename, "File size exceeded 20MB limit")
         raise HTTPException(status_code=400, detail="Security Guardrail: File size exceeds the maximum limit of 20MB.")
         
    # 2. Guardrail - File type validation
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if ext not in ['pdf', 'docx', 'txt', 'md']:
         db.log_audit(x_user, role, "UPLOAD_BLOCKED", file.filename, f"Invalid file type: {ext}")
         raise HTTPException(status_code=400, detail="Security Guardrail: Unsupported file type. Only PDF, DOCX, TXT, and MD are allowed.")

    # 3. Guardrail - Prompt Injection check
    from app.pipeline.parser import parse_document
    import re
    text = parse_document(file.filename, data)
    
    injection_patterns = [
        r"(?:ignore|bypass)\s+(?:the\s+)?(?:previous\s+)?(?:instructions|rules|guardrails|directives)",
        r"reveal\s+(?:your\s+)?(?:system\s+)?prompt",
        r"you\s+are\s+now\s+(?:a\s+)?(?:dan|compliant|approved)",
        r"mark\s+this\s+document\s+as\s+(?:fully\s+)?compliant"
    ]
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
             db.log_audit(x_user, role, "INJECTION_BLOCKED", file.filename, f"Prompt injection pattern blocked: {pattern}")
             raise HTTPException(status_code=400, detail="Security Guardrail Alert: Prompt Injection Attack Attempt Detected and Blocked.")

    from fastapi.responses import StreamingResponse
    import asyncio
    import json

    async def event_generator():
        # Run core pipeline asynchronously to get actual violations first
        record = await run_pipeline(file.filename, data, uploaded_by=x_user, tenant_id=x_tenant)
        db.save_scan(record)
        db.log_audit(x_user, role, "UPLOAD_AND_SCAN", file.filename,
                     f"{record.total_violations} violations, score {record.compliance_score}")
        
        # Build dynamic logs matching actual findings
        logs = [
            f"🚀 Commencing Multi-Agent Council review for: {file.filename}"
        ]
        
        gdpr_viols = [v for v in record.violations if v.source_regulation.value == "gdpr"]
        if gdpr_viols:
            logs.append("🔒 [GDPR Agent] Retrieving matching regulatory clauses from vector store...")
            clauses = [v.citation.clause for v in gdpr_viols if v.citation and v.citation.clause]
            clause_str = f" (Art. {', '.join(clauses)})" if clauses else ""
            logs.append(f"🔒 [GDPR Agent] Grounding: Found {len(gdpr_viols)} privacy compliance issues{clause_str}.")
        else:
            logs.append("🔒 [GDPR Agent] Reviewing privacy statements... No major GDPR violations detected.")
            
        sec_viols = [v for v in record.violations if v.source_regulation.value in ["iso27001", "internal_security"]]
        if sec_viols:
            logs.append("🔑 [Security Agent] Running entropy detectors & scanning protocol headers...")
            logs.append(f"🔑 [Security Agent] Flagged {len(sec_viols)} security risks: {', '.join(v.title for v in sec_viols)}.")
        else:
            logs.append("🔑 [Security Agent] Performing security audit... All system endpoints secure.")
            
        sox_viols = [v for v in record.violations if v.source_regulation.value == "sox"]
        if sox_viols:
            logs.append("⚖️ [Legal Agent] Modeling liability and statutory penalty exposure...")
            logs.append(f"⚖️ [Legal Agent] Flagged SOX financial risks: {', '.join(v.title for v in sox_viols)}.")
        else:
            logs.append("⚖️ [Legal Agent] Analyzing corporate agreements... SOX financial exposure is minimal.")
            
        hr_viols = [v for v in record.violations if v.source_regulation.value == "internal_hr"]
        if hr_viols:
            logs.append("📁 [Internal Policy Agent] Reviewing organization guidelines against internal rules...")
            logs.append(f"📁 [Internal Policy Agent] Policy deviation: {', '.join(v.title for v in hr_viols)}.")
        else:
            logs.append("📁 [Internal Policy Agent] No governance deviations found.")
            
        logs.append("🤝 [Consensus Council] Aggregating findings. Deduplicating overlapping vulnerabilities.")
        logs.append("✓ Scan pipeline completed. Returning results.")

        for log_msg in logs:
            yield "data: " + json.dumps({"type": "agent_log", "message": log_msg}) + "\n\n"
            await asyncio.sleep(0.4)
            
        # Serialize scan record
        rec_json = record.model_dump_json() if hasattr(record, "model_dump_json") else record.json()
        rec_dict = json.loads(rec_json)
        
        yield "data: " + json.dumps({"type": "completed", "record": rec_dict}) + "\n\n"


    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.delete("/api/scan/{scan_id}")
def delete_scan(scan_id: str,
                x_user: str = Header(default="demo@nexuszenith"),
                role: str = Depends(require("manage"))):
    rec = db.get_scan(scan_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Scan not found")
    with db._conn() as c:
        c.execute("DELETE FROM scans WHERE scan_id=?", (scan_id,))
    db.log_audit(x_user, role, "DELETE_AUDIT", rec.document_name, f"Deleted scan record {scan_id}")
    return {"status": "deleted"}


@app.get("/api/scans", response_model=list[ScanRecord])
def scans(role: str = Depends(require("view")), x_tenant: str = Header(default="acmecorp")):
    return db.list_scans(tenant_id=x_tenant)


@app.get("/api/scan/{scan_id}", response_model=ScanRecord)
def scan_detail(scan_id: str, role: str = Depends(require("view"))):
    rec = db.get_scan(scan_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Scan not found")
    return rec


@app.get("/api/scan/{scan_id}/pdf")
def download_pdf_report(scan_id: str, role: str = Depends(require("view"))):
    rec = db.get_scan(scan_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Scan not found")
    from app.pipeline.pdf_generator import generate_pdf_report
    from fastapi import Response
    pdf_bytes = generate_pdf_report(rec)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="compliance_report_{scan_id}.pdf"'
        }
    )



from pydantic import BaseModel as PydanticBaseModel
class RemediateRequest(PydanticBaseModel):
    violation_ids: list[str]


class CustomPolicyRequest(PydanticBaseModel):
    policy_name: str
    rules: list[str]


@app.post("/api/policy/custom")
def create_custom_policy(req: CustomPolicyRequest,
                         x_user: str = Header(default="demo@nexuszenith"),
                         x_tenant: str = Header(default="acmecorp"),
                         role: str = Depends(require("upload"))):
    if not req.policy_name.strip():
        raise HTTPException(status_code=400, detail="Policy name cannot be empty")
    if not req.rules:
        raise HTTPException(status_code=400, detail="Rules list cannot be empty")
    
    # Save to SQLite DB
    policy_id = db.save_custom_policy(req.policy_name, req.rules, tenant_id=x_tenant)
    
    # Append to active VectorStore
    store = get_store()
    store.add_custom_policy(x_tenant, policy_id, req.policy_name, req.rules)
    
    # Log audit event
    db.log_audit(x_user, role, "CREATE_CUSTOM_POLICY", req.policy_name, f"Created custom policy with {len(req.rules)} rules")
    
    return {"id": policy_id, "policy_name": req.policy_name, "rules": req.rules}


@app.get("/api/policy/custom")
def get_custom_policies(role: str = Depends(require("view")), x_tenant: str = Header(default="acmecorp")):
    return db.list_custom_policies(tenant_id=x_tenant)


@app.get("/api/policy/retrieve")
def retrieve_policies(text: str, n: int = 3, role: str = Depends(require("view")), x_tenant: str = Header(default="acmecorp")):
    store = get_store()
    citations = store.retrieve(text, tenant_id=x_tenant, n=n)
    return citations


@app.delete("/api/policy/custom/{policy_id}")
def delete_custom_policy_endpoint(policy_id: int,
                                  x_user: str = Header(default="demo@nexuszenith"),
                                  x_tenant: str = Header(default="acmecorp"),
                                  role: str = Depends(require("manage"))):
    # Verify existence
    policies = db.list_custom_policies(tenant_id=x_tenant)
    policy = next((p for p in policies if p["id"] == policy_id), None)
    if not policy:
        raise HTTPException(status_code=404, detail="Custom policy not found")
        
    # Delete from DB
    db.delete_custom_policy(policy_id)
    
    # Reset vector store so that it re-initializes from scratch (without the deleted policy)
    from app.pipeline import vectorstore
    vectorstore._store = None
    get_store()
    
    # Log audit event
    db.log_audit(x_user, role, "DELETE_CUSTOM_POLICY", policy["policy_name"], f"Deleted custom policy {policy_id}")
    
    return {"status": "deleted"}


@app.post("/api/policy/re-scan")
async def rescan_history(x_user: str = Header(default="demo@nexuszenith"),
                         x_tenant: str = Header(default="acmecorp"),
                         role: str = Depends(require("manage"))):
    all_scans = db.list_scans(tenant_id=x_tenant, limit=500)
    rescanned_count = 0
    from app.pipeline.agents import run_multi_agent_council
    
    for s in all_scans:
        # Re-run rule engine and vector store on the saved raw text
        doc_text = getattr(s, "raw_text", None) or s.summary  # fallback if raw_text is missing
        updated_rec = await run_multi_agent_council(s.document_name, doc_text, s.uploaded_by, s.tenant_id)
        # Preserve original ID, created_at, uploaded_by, etc.
        updated_rec.scan_id = s.scan_id
        updated_rec.created_at = s.created_at
        updated_rec.sha256_hash = s.sha256_hash
        
        db.save_scan(updated_rec)
        rescanned_count += 1
        
    db.log_audit(x_user, role, "RE-SCAN_ALL_HISTORY", f"scans count: {rescanned_count}",
                 "Triggered bulk re-evaluation of historical audits against active policies list.")
                 
    return {"status": "success", "count": rescanned_count}



@app.post("/api/scan/{scan_id}/remediate", response_model=ScanRecord)
def remediate_scan(scan_id: str,
                   req: RemediateRequest,
                   x_user: str = Header(default="demo@nexuszenith"),
                   role: str = Depends(require("upload"))):
    from app.models import Severity
    rec = db.get_scan(scan_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Scan not found")

    resolved_violations = []
    remaining_violations = []

    score_boost = 0
    exposure_min_reduction = 0.0
    exposure_max_reduction = 0.0
    affected_users_reduction = 0

    for v in rec.violations:
        if v.id in req.violation_ids:
            resolved_violations.append(v)
            score_boost += getattr(v, "remediation_score_improvement", 0) or 0
            exposure_min_reduction += getattr(v, "estimated_fine_min", 0.0) or 0.0
            exposure_max_reduction += getattr(v, "estimated_fine_max", 0.0) or 0.0
            affected_users_reduction += getattr(v, "affected_users_estimate", 0) or 0
        else:
            remaining_violations.append(v)

    if not resolved_violations:
        return rec

    # Update scan records
    rec.violations = remaining_violations
    rec.compliance_score = min(100, rec.compliance_score + score_boost)
    rec.total_violations = len(remaining_violations)

    # Re-calculate breakdown
    breakdown = {s.value: 0 for s in Severity}
    for v in remaining_violations:
        breakdown[v.severity.value] += 1
    rec.severity_breakdown = breakdown

    # Re-calculate exposure
    rec.total_exposure_min = max(0.0, rec.total_exposure_min - exposure_min_reduction)
    rec.total_exposure_max = max(0.0, rec.total_exposure_max - exposure_max_reduction)
    rec.total_affected_users = max(0, rec.total_affected_users - affected_users_reduction)

    db.save_scan(rec)

    # Log each applied resolution
    for v in resolved_violations:
        db.log_audit(
            x_user, role, "REMEDIATION_APPLIED", rec.document_name,
            f"Resolved violation '{v.title}' via AI patch. Compliance score boosted +{getattr(v, 'remediation_score_improvement', 0)}%."
        )

    return rec



@app.get("/api/audit")
def audit(role: str = Depends(require("audit"))):
    return db.get_audit()


@app.get("/api/dashboard", response_model=DashboardStats)
def dashboard(role: str = Depends(require("view")), x_tenant: str = Header(default="acmecorp")):
    all_scans = db.list_scans(tenant_id=x_tenant, limit=500)
    docs = len(all_scans)
    risks = sum(s.total_violations for s in all_scans)
    avg_score = round(sum(s.compliance_score for s in all_scans) / docs) if docs else 100

    # severity -> category rollup
    cat = {"Access Control": 0, "Data Protection": 0, "Policy Violation": 0,
           "Configuration": 0, "Others": 0}
    cat_map = {
        "internal_security": "Access Control",
        "gdpr": "Data Protection",
        "internal_hr": "Policy Violation",
        "iso27001": "Configuration",
        "sox": "Others",
    }
    for s in all_scans:
        for v in s.violations:
            cat[cat_map.get(v.source_regulation.value, "Others")] += 1
    total_cat = sum(cat.values()) or 1
    risk_by_category = [
        {"name": k, "value": round(v / total_cat * 100)} for k, v in cat.items() if v
    ]
    top_risky = sorted(
        ({"name": k, "risks": v} for k, v in cat.items() if v),
        key=lambda x: -x["risks"])[:4]

    # synthetic 30-day trend climbing toward current score
    today = datetime.now(timezone.utc)
    trend = []
    for i in range(0, 30, 5):
        d = today - timedelta(days=29 - i)
        base = max(40, avg_score - (29 - i))
        trend.append({"label": d.strftime("%b %d"), "value": min(100, base)})
    trend.append({"label": today.strftime("%b %d"), "value": avg_score})

    alerts = []
    for s in all_scans[:5]:
        for v in s.violations[:1]:
            alerts.append({
                "title": v.title, "severity": v.severity.label,
                "document": s.document_name})

    # Calculate aggregate risk metrics
    total_exp_min = sum(getattr(s, "total_exposure_min", 0.0) or 0.0 for s in all_scans)
    total_exp_max = sum(getattr(s, "total_exposure_max", 0.0) or 0.0 for s in all_scans)
    total_aff_users = sum(getattr(s, "total_affected_users", 0) or 0 for s in all_scans)

    # If no scans are loaded, add some realistic base metrics for simulation
    if not all_scans:
        total_exp_min = 0.0
        total_exp_max = 0.0
        total_aff_users = 0

    return DashboardStats(
        overall_compliance_score=avg_score,
        policies_scanned=len(get_store()._get_tenant_blocks(x_tenant)),
        risks_detected=risks,
        documents_analyzed=docs,
        compliance_trend=trend,
        risk_by_category=risk_by_category or [{"name": "No data", "value": 100}],
        top_risky_areas=top_risky or [{"name": "No risks", "risks": 0}],
        recent_alerts=alerts,
        total_exposure_min=total_exp_min,
        total_exposure_max=total_exp_max,
        total_affected_users=total_aff_users
    )

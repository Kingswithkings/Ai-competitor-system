from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.ai_engine import analyze_business
from app.database import init_db, save_audit, list_audits, get_audit
from app.pdf_report import generate_pdf_report

app = FastAPI(title="AI Competitor System")


class AuditRequest(BaseModel):
    website: str
    industry: str


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {"message": "AI Competitor System API is running"}


@app.post("/audit")
def run_audit(request: AuditRequest):
    try:
        result = analyze_business(request.website, request.industry)

        target = result.get("target_business", {})
        business_name = target.get("business_name", "")
        website = target.get("website", request.website)
        industry = target.get("industry", request.industry)
        summary = target.get("summary", "")

        audit_id = save_audit(
            business_name=business_name,
            website=website,
            industry=industry,
            summary=summary,
            result=result,
        )

        pdf_path = generate_pdf_report(audit_id, result)

        return {
            "audit_id": audit_id,
            "pdf_path": pdf_path,
            "result": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audits")
def get_audits():
    return list_audits()


@app.get("/audits/{audit_id}")
def fetch_audit(audit_id: int):
    audit = get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


@app.get("/audits/{audit_id}/pdf")
def download_audit_pdf(audit_id: int):
    audit = get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    pdf_path = generate_pdf_report(audit_id, audit["result_json"])
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"audit_{audit_id}.pdf",
    )
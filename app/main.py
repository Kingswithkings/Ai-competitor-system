from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.schemas import AuditRequest
from app.ai_engine import analyze_business
from app.database import init_db, save_audit, list_audits, get_audit


app = FastAPI(title="1stkings AI Competitor System")


def build_pdf_report(audit_id: int, audit_data: dict) -> str:
    try:
        from app.pdf_report import generate_pdf_report
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="PDF generation is unavailable because required dependencies are not installed.",
        ) from exc

    return generate_pdf_report(audit_id, audit_data)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {"message": "AI Competitor System API is running"}


@app.post("/audit")
def run_audit(request: AuditRequest):
    try:
        result = analyze_business(
            website=request.website,
            industry=request.industry,
            business_name=request.business_name,
            location=request.location,
        )

        target = result.get("target_business", {})
        audit_id = save_audit(
            business_name=target.get("business_name", ""),
            website=target.get("website", request.website),
            industry=target.get("industry", request.industry),
            location=target.get("location", request.location or ""),
            summary=target.get("summary", ""),
            result=result,
        )

        pdf_path = None
        try:
            pdf_path = build_pdf_report(audit_id, result)
        except HTTPException:
            pdf_path = None

        return {
            "audit_id": audit_id,
            "pdf_path": pdf_path,
            "result": result,
        }

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audits")
def get_all_audits():
    return list_audits()


@app.get("/audits/{audit_id}")
def get_single_audit(audit_id: int):
    audit = get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


@app.get("/audits/{audit_id}/pdf")
def download_audit_pdf(audit_id: int):
    audit = get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    pdf_path = build_pdf_report(audit_id, audit["result_json"])
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"audit_{audit_id}.pdf",
    )

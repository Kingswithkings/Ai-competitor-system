from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.ai_engine import analyze_business

app = FastAPI(title="AI Competitor System")


class AuditRequest(BaseModel):
    website: str
    industry: str


@app.get("/")
def root():
    return {"message": "AI Competitor System API is running"}


@app.post("/audit")
def run_audit(request: AuditRequest):
    try:
        return analyze_business(request.website, request.industry)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
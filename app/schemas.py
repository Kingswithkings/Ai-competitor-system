from pydantic import BaseModel, Field
from typing import List, Optional


class AuditRequest(BaseModel):
    website: str
    industry: str
    business_name: Optional[str] = None
    location: Optional[str] = None


class CompetitorItem(BaseModel):
    name: str
    website: str
    presence: int = 0
    engagement: int = 0
    automation: int = 0
    strength: str = ""
    weighted_score: float = 0.0
    grade: str = ""


class AIToolRecommendation(BaseModel):
    business_need: str
    tool_category: str
    suggested_tools: List[str] = Field(default_factory=list)
    reason: str
    priority: str
    implementation_type: str
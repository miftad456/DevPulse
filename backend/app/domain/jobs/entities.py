from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class Job(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    job_type: str  # remote, onsite, hybrid
    experience_level: str
    tech_stack: List[str]
    description: str
    source: str
    url: str
    created_at: datetime = datetime.utcnow()

class JobIngestRequest(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    job_type: str
    experience_level: str
    tech_stack: List[str]
    description: str
    source: str
    url: str

from pydantic import BaseModel
from typing import Optional, List

class UserPreferences(BaseModel):
    job_role: Optional[str] = None
    experience_level: Optional[str] = None
    tech_stack: Optional[List[str]] = []
    preferred_job_type: Optional[str] = None
    preferred_location: Optional[str] = None
    expected_salary_range: Optional[str] = None

class OnboardingRequest(UserPreferences):
    pass

class OnboardingPatchRequest(BaseModel):
    job_role: Optional[str] = None
    experience_level: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    preferred_job_type: Optional[str] = None
    preferred_location: Optional[str] = None
    expected_salary_range: Optional[str] = None

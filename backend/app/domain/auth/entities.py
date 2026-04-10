from pydantic import BaseModel, EmailStr
from typing import Optional, List

class User(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str   # ✅ FIXED (was hashed_password)
    experience_level: Optional[str] = None
    job_type: Optional[str] = None
    skills: Optional[List[str]] = []
    onboarding_completed: bool = False
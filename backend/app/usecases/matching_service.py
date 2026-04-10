from app.infrastructure.jobs.repository import JobRepository
from app.infrastructure.onboarding.repository import OnboardingRepository
from typing import List, Dict

class JobUseCase:
    def __init__(self, job_repo: JobRepository, user_repo: OnboardingRepository):
        self.job_repo = job_repo
        self.user_repo = user_repo

    async def match_jobs_for_user(self, user_id: str) -> List[Dict]:
        """
        Fetches user preferences and matches against available jobs, scoring them.
        """
        user = await self.user_repo.get_user_preferences(user_id)
        if not user or not user.get("onboarding_completed"):
            raise ValueError("User preferences not found or onboarding incomplete")

        pref_role = (user.get("job_role") or "").lower()
        pref_level = (user.get("experience_level") or "").lower()
        pref_type = (user.get("job_type") or "").lower()
        pref_skills = [s.lower() for s in user.get("skills", [])]

        jobs = await self.job_repo.get_jobs_for_matching()
        matched_jobs = []

        for job in jobs:
            score = 0
            
            # Exact role match
            if pref_role and pref_role in job["title"].lower():
                score += 3
            elif pref_role and pref_role in job.get("job_role", job["title"]).lower():
                score += 3

            # Level match
            if pref_level and pref_level == job["experience_level"].lower():
                score += 2

            # Job Type match
            if pref_type and pref_type == job["job_type"].lower():
                score += 2

            # Tech Stack match
            job_stack = [s.lower() for s in job.get("tech_stack", [])]
            for skill in pref_skills:
                if skill in job_stack:
                    score += 1
            
            # Remove ObjectId before returning
            job["_id"] = str(job["_id"])
            
            # Include score
            job["match_score"] = score
            
            # Only include jobs that have a reasonable match (e.g. score > 0)
            if score > 0:
                matched_jobs.append(job)

        # Sort jobs by match_score descending
        matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        return matched_jobs

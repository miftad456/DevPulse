from app.infrastructure.jobs.repository import JobRepository
from app.infrastructure.onboarding.repository import OnboardingRepository
from typing import List, Dict

class JobUseCase:
    def __init__(self, job_repo: JobRepository, user_repo: OnboardingRepository):
        self.job_repo = job_repo
        self.user_repo = user_repo

    def score_jobs_for_user(self, user: Dict, jobs: List[Dict]) -> List[Dict]:
        """
        Matches pre-fetched user preferences against pre-fetched jobs using scoring logic.
        """
        if not user.get("onboarding_completed"):
            return []

        pref_role = (user.get("job_role") or "").lower()
        pref_level = (user.get("experience_level") or "").lower()
        pref_type = (user.get("job_type") or "").lower()
        pref_skills = [s.lower() for s in user.get("skills", [])]

        matched_jobs = []

        for job in jobs:
            score = 0
            
            # Exact role match
            if pref_role and pref_role in job["title"].lower():
                score += 3
            elif pref_role and (job.get("job_role") and pref_role in job["job_role"].lower()):
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
            
            # Include score if > 0
            if score > 0:
                # create copy so we don't modify the source for other users
                job_dict = dict(job)
                job_dict["_id"] = str(job_dict["_id"])
                job_dict["match_score"] = score
                matched_jobs.append(job_dict)

        # Sort jobs by match_score descending
        matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        return matched_jobs

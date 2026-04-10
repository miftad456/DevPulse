from app.domain.onboarding.entities import OnboardingRequest, OnboardingPatchRequest
from app.infrastructure.onboarding.repository import OnboardingRepository

class OnboardingUseCase:
    def __init__(self, repo: OnboardingRepository):
        self.repo = repo

    async def complete_onboarding(self, user_id: str, preferences: OnboardingRequest):
        updates = preferences.model_dump(exclude_unset=True)
        # Map fields to what's expected or add new ones
        updates["onboarding_completed"] = True
        
        # In case the auth user model uses 'skills' but onboarding uses 'tech_stack'
        if "tech_stack" in updates:
            updates["skills"] = updates.pop("tech_stack")
        if "preferred_job_type" in updates:
            updates["job_type"] = updates.pop("preferred_job_type")

        # Create indexes specifically for n8n matching (just an admin/startup action, but making sure they exist)
        # Using db.users.create_index([("job_role", 1), ("experience_level", 1), ("skills", 1)])
        # is normally done at startup, we just ensure records match expected shape here.

        success = await self.repo.update_user_preferences(user_id, updates)
        if not success:
            raise ValueError("Failed to complete onboarding. User not found.")
        return updates

    async def update_onboarding(self, user_id: str, patch: OnboardingPatchRequest):
        updates = patch.model_dump(exclude_unset=True)
        if "tech_stack" in updates:
            updates["skills"] = updates.pop("tech_stack")
        if "preferred_job_type" in updates:
            updates["job_type"] = updates.pop("preferred_job_type")

        if not updates:
            return True

        success = await self.repo.update_user_preferences(user_id, updates)
        if not success:
            raise ValueError("User not found or update failed.")
        return updates

    async def get_onboarding_status(self, user_id: str):
        user = await self.repo.get_user_preferences(user_id)
        if not user:
            raise ValueError("User not found")
        
        return {
            "onboarding_completed": user.get("onboarding_completed", False),
            "preferences": {
                "job_role": user.get("job_role"),
                "experience_level": user.get("experience_level"),
                "tech_stack": user.get("skills", []),
                "preferred_job_type": user.get("job_type"),
                "preferred_location": user.get("preferred_location"),
                "expected_salary_range": user.get("expected_salary_range")
            }
        }

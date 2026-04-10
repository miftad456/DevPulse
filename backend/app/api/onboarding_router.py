from fastapi import APIRouter, Depends, HTTPException
from app.domain.onboarding.entities import OnboardingRequest, OnboardingPatchRequest
from app.infrastructure.onboarding.repository import OnboardingRepository
from app.usecases.onboarding_usecases import OnboardingUseCase
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

def get_onboarding_usecase():
    repo = OnboardingRepository()
    return OnboardingUseCase(repo)

@router.post("")
async def complete_onboarding(
    req: OnboardingRequest,
    user_id: str = Depends(get_current_user),
    usecase: OnboardingUseCase = Depends(get_onboarding_usecase)
):
    try:
        updated = await usecase.complete_onboarding(user_id, req)
        return {"message": "Onboarding completed successfully", "preferences": updated}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("")
async def update_onboarding(
    req: OnboardingPatchRequest,
    user_id: str = Depends(get_current_user),
    usecase: OnboardingUseCase = Depends(get_onboarding_usecase)
):
    try:
        updated = await usecase.update_onboarding(user_id, req)
        return {"message": "Preferences updated successfully", "preferences": updated}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("")
async def get_onboarding(
    user_id: str = Depends(get_current_user),
    usecase: OnboardingUseCase = Depends(get_onboarding_usecase)
):
    try:
        status = await usecase.get_onboarding_status(user_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

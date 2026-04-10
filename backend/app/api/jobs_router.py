from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.jobs.entities import JobIngestRequest, Job
from app.infrastructure.jobs.repository import JobRepository
from app.api.dependencies import verify_api_key

router = APIRouter(prefix="/jobs", tags=["jobs"])

def get_job_repo():
    return JobRepository()

@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_job(
    request: JobIngestRequest,
    api_key: str = Depends(verify_api_key),
    repo: JobRepository = Depends(get_job_repo)
):
    """
    Ingest a new job scraped by external systems like n8n.
    Requires `x-api-key` in headers.
    """
    job_doc = Job(**request.model_dump())
    success = await repo.insert_job(job_doc.model_dump())
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job with this URL already exists"
        )
    return {"message": "Job ingested successfully", "job_url": job_doc.url}

from app.usecases.matching_service import JobUseCase
from app.api.dependencies import get_current_user
from app.infrastructure.onboarding.repository import OnboardingRepository

def get_job_usecase():
    return JobUseCase(JobRepository(), OnboardingRepository())

@router.get("/match")
async def match_jobs(
    user_id: str = Depends(get_current_user),
    usecase: JobUseCase = Depends(get_job_usecase)
):
    """
    Match ingested jobs scoring them against current user's preferences.
    Requires JWT token and completed onboarding.
    """
    try:
        matched_jobs = await usecase.match_jobs_for_user(user_id)
        return {"message": "Jobs matched successfully", "matches": matched_jobs}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

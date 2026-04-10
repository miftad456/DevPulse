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

from app.infrastructure.external.n8n_service import N8nService

import asyncio
WEBHOOK_SEMAPHORE = asyncio.Semaphore(50)

@router.post("/run-batch-match")
async def run_batch_match(
    api_key: str = Depends(verify_api_key),
    usecase: JobUseCase = Depends(get_job_usecase)
):
    """
    Triggered by an n8n Cron Workflow to run matching strictly ONCE.
    Iterates over all onboarded users and pushes matched notifications to n8n Webhook.
    """
    # 1. Distributed Lock Acquisition
    locked = await usecase.job_repo.acquire_batch_lock()
    if not locked:
        return {"message": "Batch already running globally", "matched_users_notified": 0}
        
    try:
        from app.infrastructure.onboarding.repository import OnboardingRepository
        user_repo = OnboardingRepository()
        n8n = N8nService()
        
        # 2. Recover Stuck Jobs from Failed Nodes
        await usecase.job_repo.recover_stuck_jobs(timeout_minutes=30)
        
        # 3. Scalability Fix + Atomic State Transitions
        # Atomically extracts and locks pending jobs straight into processing
        unmatched_jobs = await usecase.job_repo.get_and_lock_pending_jobs()
        if not unmatched_jobs:
            return {"message": "No new jobs to match", "matched_users_notified": 0}
            
        users = await user_repo.get_all_onboarded_users()
        tasks = []
        
        import uuid
        batch_id = str(uuid.uuid4())
        
        async def bounded_send(u, j, bid):
            async with WEBHOOK_SEMAPHORE:
                return await n8n.send_matched_jobs(u, j, bid)
        
        # Memory/N+1 Query Resolution mapped into Race Safeties
        check_ids = [j["_id"] for j in unmatched_jobs]
        
        for user in users:
            try:
                # 5. FINAL SAFETY RECHECK
                # Validate job states legitimately still reflect active "processing" before parsing
                states = await usecase.job_repo.collection.find({"_id": {"$in": check_ids}}, {"status": 1}).to_list(length=None)
                state_map = {str(doc["_id"]): doc.get("status") for doc in states}
                
                safe_jobs = []
                for job in unmatched_jobs:
                    if state_map.get(str(job["_id"])) == "processing":
                        safe_jobs.append(job)
                        
                if not safe_jobs:
                    continue
                    
                matched_jobs = usecase.score_jobs_for_user(user, safe_jobs)
                if matched_jobs:
                    tasks.append(bounded_send(user, matched_jobs, batch_id))
            except Exception as e:
                print(f"Error matching for user {user['_id']}: {e}")
                
        # Send Webhooks non-blocking
        dispatched_count = 0
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            dispatched_count = sum(1 for r in results if r is True)
            
        # Finalize and log out
        job_ids = [str(j["_id"]) for j in unmatched_jobs]
        await usecase.job_repo.update_job_status(job_ids, "matched")
                
        return {"message": "Batch match execution completed", "matched_users_notified": dispatched_count}
    finally:
        # Guarantee lock release completely independent of crash logic
        await usecase.job_repo.release_batch_lock()

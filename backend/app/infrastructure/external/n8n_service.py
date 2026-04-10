import os
import httpx

from pymongo.errors import DuplicateKeyError
from datetime import datetime

class N8nService:
    def __init__(self):
        self.webhook_url = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/job-match")
        from app.infrastructure.database.mongo import get_database
        self.db = get_database()

    async def send_matched_jobs(self, user_info: dict, jobs: list, batch_id: str):
        """
        Pushes matched jobs alongside user details to the n8n webhook, using persistent DB idempotency.
        """
        user_id = str(user_info.get("_id", ""))
        valid_jobs = []
        
        for j in jobs:
            idem_key = f"{batch_id}_{j.get('_id')}_{user_id}"
            try:
                # Atomic DB insert ensures true idempotency
                await self.db.processed_webhooks.insert_one({
                    "_id": idem_key,
                    "created_at": datetime.utcnow()
                })
                valid_jobs.append(j)
            except DuplicateKeyError:
                # If key exists, it has already been processed globally
                pass

        if not valid_jobs:
            return True  # Avoid duplicates logically

        payload = {
            "user": {
                "id": user_id,
                "email": user_info.get("email"),
                "username": user_info.get("username"),
            },
            "jobs": [
                {
                    "title": j.get("title"),
                    "company": j.get("company"),
                    "url": j.get("url"),
                    "match_score": j.get("match_score"),
                    "source": j.get("source")
                } for j in valid_jobs
            ]
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.webhook_url, json=payload, timeout=10.0)
                response.raise_for_status()
                return True
            except Exception as e:
                print(f"Failed to trigger n8n webhook: {e}")
                return False

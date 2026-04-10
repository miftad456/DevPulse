import os
import httpx

class N8nService:
    def __init__(self):
        self.webhook_url = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/job-match")

    async def send_matched_jobs(self, user_info: dict, jobs: list):
        """
        Pushes matched jobs alongside user details to the n8n webhook.
        n8n will handle routing this to Telegram/Email.
        """
        if not jobs:
            return  # No point in sending empty matches

        payload = {
            "user": {
                "id": str(user_info.get("_id", "")),
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
                } for j in jobs
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

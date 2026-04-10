from pymongo.errors import DuplicateKeyError
from app.infrastructure.database.mongo import get_database

class JobRepository:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.jobs

    async def insert_job(self, job_data: dict) -> bool:
        """
        Inserts a generic job into the jobs collection.
        Returns True if inserted, False if duplicate.
        """
        try:
            await self.collection.insert_one(job_data)
            return True
        except DuplicateKeyError:
            return False

    async def get_jobs_for_matching(self, limit: int = 50) -> list:
        """
        Retrieves recent jobs from the database for matching purposes.
        """
        cursor = self.collection.find().sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

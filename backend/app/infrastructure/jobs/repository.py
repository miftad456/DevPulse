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

    async def recover_stuck_jobs(self, timeout_minutes: int = 30):
        """
        Resets jobs stuck in 'processing' state past the time threshold back to 'pending'.
        """
        from datetime import datetime, timedelta
        threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        await self.collection.update_many(
            {"status": "processing", "updated_at": {"$lt": threshold}},
            {"$set": {"status": "pending", "updated_at": datetime.utcnow()}}
        )

    async def get_and_lock_pending_jobs(self) -> list:
        """
        Retrieves pending jobs and atomically locks them into processing state.
        """
        cursor = self.collection.find({"status": "pending"})
        jobs = await cursor.to_list(length=None)
        
        if jobs:
            from bson.objectid import ObjectId
            from datetime import datetime
            job_ids = [j["_id"] for j in jobs]
            await self.collection.update_many(
                {"_id": {"$in": job_ids}, "status": "pending"},
                {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
            )
        return jobs

    async def update_job_status(self, job_ids: list, new_status: str):
        """
        Updates the status of multiple jobs explicitly.
        """
        if job_ids:
            from bson.objectid import ObjectId
            from datetime import datetime
            oids = [ObjectId(jid) if isinstance(jid, str) else jid for jid in job_ids]
            await self.collection.update_many(
                {"_id": {"$in": oids}}, 
                {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
            )

    async def acquire_batch_lock(self, timeout_minutes: int = 30) -> bool:
        """
        Uses MongoDB to establish a globally distributed batch lock with a safe TTL expiry via an atomic findOneAndUpdate.
        """
        from datetime import datetime, timedelta
        from pymongo import ReturnDocument
        from pymongo.errors import DuplicateKeyError
        
        now = datetime.utcnow()
        threshold = now - timedelta(minutes=timeout_minutes)
        
        # Ensure the document strictly exists before attempt
        try:
            await self.db.system_locks.insert_one({"_id": "batch_lock", "locked": False, "updated_at": now})
        except DuplicateKeyError:
            pass

        # Atomic find one and update
        result = await self.db.system_locks.find_one_and_update(
            {
                "_id": "batch_lock",
                "$or": [
                    {"locked": False},
                    {"locked": True, "updated_at": {"$lt": threshold}}
                ]
            },
            {"$set": {"locked": True, "updated_at": now}},
            return_document=ReturnDocument.AFTER
        )
        return result is not None

    async def release_batch_lock(self):
        """
        Releases the global database batch lock.
        """
        await self.db.system_locks.update_one(
            {"_id": "batch_lock"},
            {"$set": {"locked": False}}
        )

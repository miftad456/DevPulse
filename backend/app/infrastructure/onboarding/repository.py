from bson.objectid import ObjectId
from app.infrastructure.database.mongo import get_database

class OnboardingRepository:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.users

    async def update_user_preferences(self, user_id: str, updates: dict):
        """Updates the given user preferences in the users collection."""
        if "_id" not in updates: # safety
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        return False

    async def get_user_preferences(self, user_id: str):
        """Fetches the user document to retrieve preferences."""
        user = await self.collection.find_one({"_id": ObjectId(user_id)})
        return user

    async def get_all_onboarded_users(self):
        """Fetches all users who have completed onboarding for batch matching."""
        cursor = self.collection.find({"onboarding_completed": True})
        return await cursor.to_list(length=None)

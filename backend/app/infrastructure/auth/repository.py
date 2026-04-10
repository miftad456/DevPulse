from app.domain.auth.entities import User
from app.infrastructure.database.mongo import get_database
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthRepository:
    def __init__(self):
        # We don't access the DB here because it might not be connected yet.
        self._collection = None

    def get_collection(self):
        """Lazy access to the collection to ensure DB is connected."""
        if self._collection is None:
            db = get_database()
            if db is None:
                raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
            self._collection = db["users"]
        return self._collection

    async def create_user(self, user: User):
        collection = self.get_collection()
        user_dict = user.dict()

        # ✅ HASH HERE (correct place)
        user_dict["hashed_password"] = pwd_context.hash(user_dict.pop("password"))

        result = await collection.insert_one(user_dict)
        return result.inserted_id

    async def find_by_email_or_username(self, email_or_username: str):
        collection = self.get_collection()
        doc = await collection.find_one({
            "$or": [{"email": email_or_username}, {"username": email_or_username}]
        })
        return doc

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
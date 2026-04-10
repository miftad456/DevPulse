from datetime import datetime, timedelta
from typing import Dict
from jose import jwt
from app.infrastructure.auth.repository import AuthRepository
from app.domain.auth.entities import User
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

class AuthUseCase:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    async def register_user(self, user: User):
        existing = await self.repo.find_by_email_or_username(user.email)
        if existing:
            raise ValueError("User already exists with this email or username")
        return await self.repo.create_user(user)

    async def login_user(self, email_or_username: str, password: str) -> Dict:
        user = await self.repo.find_by_email_or_username(email_or_username)
        if not user or not self.repo.verify_password(password, user["hashed_password"]):
            raise ValueError("Invalid credentials")

        access_token = self.create_access_token({"sub": user["username"]})
        refresh_token = self.create_refresh_token({"sub": user["username"]})
        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "user": {
                "id": str(user["_id"]) if "_id" in user else None,
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "username": user.get("username"),
                "email": user.get("email"),
                "experience_level": user.get("experience_level"),
                "job_type": user.get("job_type"),
                "skills": user.get("skills", []),
            }
        }

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
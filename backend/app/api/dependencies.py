from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import jwt, JWTError
from app.core.config import SECRET_KEY, ALGORITHM
from app.infrastructure.auth.repository import AuthRepository
import os

security = HTTPBearer()
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key_header: str = Security(api_key_header)):
    # You should define N8N_API_KEY in your .env
    expected_api_key = os.environ.get("N8N_API_KEY", "default-dev-api-key")
    if api_key_header == expected_api_key:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # We need the user\_id for onboarding operations.
        # Could improve this by storing user_id in the token 'sub' directly, 
        # but for now we look up by username.
        repo = AuthRepository()
        user = await repo.find_by_email_or_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return str(user["_id"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr , Field
from app.usecases.auth_usecases import AuthUseCase
from app.infrastructure.auth.repository import AuthRepository
from app.domain.auth.entities import User

router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_repo():
    return AuthRepository()

def get_auth_usecase():
    repo = get_auth_repo()
    return AuthUseCase(repo)



class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)  # ✅ FIX
    confirm_password: str

class LoginRequest(BaseModel):
    email_or_username: str
    password: str

@router.post("/register")
async def register(req: RegisterRequest, use_case: AuthUseCase = Depends(get_auth_usecase)):
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    user = User(
        first_name=req.first_name,
        last_name=req.last_name,
        username=req.username,
        email=req.email,
        password=req.password
    )
    try:
        user_id = await use_case.register_user(user)
        return {"message": "User registered", "user_id": str(user_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(req: LoginRequest, use_case: AuthUseCase = Depends(get_auth_usecase)):
    try:
        tokens = await use_case.login_user(req.email_or_username, req.password)
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
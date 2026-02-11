"""Authentication API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user_id: str
    role: str
    token: str
    message: str

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint. 
    EXPERIMENTAL: Hardcoded credentials for prototype.
    """
    if request.username == "admin" and request.password == "admin123":
        return {
            "user_id": "admin",
            "role": "curator", # Admin gets curator role
            "token": "simulated-admin-token-xyz", 
            "message": "Login successful"
        }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

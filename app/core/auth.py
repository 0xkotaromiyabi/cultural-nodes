"""Authentication module for Cultural AI RAG system.

Uses simple header-based authentication for this iteration.
"""

from fastapi import HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: str
    role: str

async def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
) -> User:
    """Get current user from headers.
    
    In a real production system, this would verify a JWT token.
    For this prototype, we trust the headers (simulated auth).
    """
    if not x_user_id:
        return User(id="anonymous", role="contributor")
        
    return User(id=x_user_id, role=x_user_role or "contributor")

async def require_curator(user: User = Depends(get_current_user)) -> User:
    """Dependency to require curator role."""
    if user.role not in ["curator", "admin"]:
        raise HTTPException(
            status_code=403, 
            detail="Permission denied. Curator role required."
        )
    return user

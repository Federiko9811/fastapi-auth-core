"""
User endpoints for profile management.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current authenticated user's profile.

    Args:
        current_user: The authenticated user from the access token.

    Returns:
        The current user's profile data.
    """
    return current_user

from typing import List, Tuple
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import UserModel, SessionModel
from app.services.auth_service import AuthService

COOKIE_NAME = "flowpilot_session"


async def get_current_user_and_session(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Tuple[UserModel, SessionModel]:
    """
    1. Authenticated User Check:
    Reads HTTP-only session cookie or Authorization Bearer header.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing or invalid session cookie.",
        )

    result = await AuthService.get_user_by_session_token(token, db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again.",
        )

    user, session = result
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user, session


async def get_current_user(
    auth_data: Tuple[UserModel, SessionModel] = Depends(get_current_user_and_session)
) -> UserModel:
    return auth_data[0]


def require_role(allowed_roles: List[str]):
    """
    2. Authorization Check (RBAC):
    Verifies user has at least one of the specified roles (e.g. USER, ADMIN).
    """
    async def role_checker(user: UserModel = Depends(get_current_user)) -> UserModel:
        user_roles = [r.name for r in user.roles]
        # ADMIN role overrides all role checks
        if "ADMIN" in user_roles:
            return user

        has_permission = any(role in user_roles for role in allowed_roles)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Authorization failure. Required role: {', '.join(allowed_roles)}.",
            )
        return user

    return role_checker


def verify_resource_ownership(resource_owner_id: str, user: UserModel):
    """
    3. Resource Ownership Check:
    Verifies resource belongs to current_user.id or current_user is ADMIN.
    """
    user_roles = [r.name for r in user.roles]
    if "ADMIN" in user_roles:
        return True

    if resource_owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not own this resource.",
        )
    return True

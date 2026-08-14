from typing import List, Tuple
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user_and_session, get_current_user, COOKIE_NAME, require_role
from app.models.user import UserModel, SessionModel
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    SessionResponse,
    AuthStatusResponse,
    ForgotPasswordRequest,
    ResetPasswordConfirmRequest,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService.register_user(req, db)
        role_names = [r.name for r in user.roles]
        return UserResponse(
            id=user.id,
            email=user.email,
            fullName=user.full_name,
            isActive=user.is_active,
            isVerified=user.is_verified,
            roles=role_names,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=AuthStatusResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    device_info = request.headers.get("User-Agent", "Unknown Browser / Device")
    ip_address = request.client.host if request.client else "127.0.0.1"

    try:
        user, raw_session_token = await AuthService.login_user(
            email=req.email,
            password=req.password,
            device_info=device_info,
            ip_address=ip_address,
            db=db,
        )

        # Set Secure HTTP-Only session cookie
        response.set_cookie(
            key=COOKIE_NAME,
            value=raw_session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 3600,  # 30 days
            path="/",
        )

        role_names = [r.name for r in user.roles]
        user_resp = UserResponse(
            id=user.id,
            email=user.email,
            fullName=user.full_name,
            isActive=user.is_active,
            isVerified=user.is_verified,
            roles=role_names,
        )

        return AuthStatusResponse(user=user_resp, currentSessionId="active")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    auth_data: Tuple[UserModel, SessionModel] = Depends(get_current_user_and_session),
    db: AsyncSession = Depends(get_db)
):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if token:
        await AuthService.logout_session(token, db)

    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"success": True, "message": "Logged out successfully."}


@router.post("/logout-all")
async def logout_all_sessions(
    response: Response,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await AuthService.logout_all_user_sessions(user.id, db)
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"success": True, "message": "All active sessions have been terminated."}


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserModel = Depends(get_current_user)):
    role_names = [r.name for r in user.roles]
    return UserResponse(
        id=user.id,
        email=user.email,
        fullName=user.full_name,
        isActive=user.is_active,
        isVerified=user.is_verified,
        roles=role_names,
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def get_active_sessions(
    auth_data: Tuple[UserModel, SessionModel] = Depends(get_current_user_and_session),
    db: AsyncSession = Depends(get_db)
):
    user, current_session = auth_data
    res = await db.execute(
        select(SessionModel).where(
            SessionModel.user_id == user.id,
            SessionModel.is_active == True,
        ).order_by(SessionModel.last_accessed_at.desc())
    )
    sessions = res.scalars().all()

    return [
        SessionResponse(
            id=s.id,
            deviceInfo=s.device_info,
            ipAddress=s.ip_address,
            isActive=s.is_active,
            expiresAt=s.expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            createdAt=s.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            isCurrentSession=(s.id == current_session.id),
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(SessionModel).where(
            SessionModel.id == session_id,
            SessionModel.user_id == user.id
        )
    )
    target_session = res.scalar_one_or_none()
    if not target_session:
        raise HTTPException(status_code=404, detail="Session record not found.")

    target_session.is_active = False
    await db.commit()
    return {"success": True, "message": f"Session {session_id} revoked."}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await AuthService.request_password_reset(req.email, db)
    return {"success": True, "message": "If an account exists, a password reset email has been dispatched."}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordConfirmRequest, db: AsyncSession = Depends(get_db)):
    try:
        await AuthService.reset_password(req.token, req.newPassword, db)
        return {"success": True, "message": "Password successfully reset. Please log in with your new password."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-email")
async def verify_email(req: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    success = await AuthService.verify_email_token(req.token, db)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
    return {"success": True, "message": "Email address verified successfully."}


@router.get("/oauth/google/url")
async def get_google_oauth_url():
    """Returns Google OAuth2 authorization URL configuration."""
    redirect_uri = "http://localhost:3000/auth/oauth/google/callback"
    client_id = "flowpilot-google-client-id.apps.googleusercontent.com"
    scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"
    return {"url": auth_url, "provider": "Google OAuth2"}


@router.get("/admin/test-rbac", response_model=dict)
async def admin_only_endpoint(admin_user: UserModel = Depends(require_role(["ADMIN"]))):
    """Protected endpoint restricted exclusively to ADMIN users."""
    return {"status": "ok", "message": f"Welcome Admin {admin_user.full_name}. RBAC authorization verified."}

from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import (
    UserModel,
    RoleModel,
    UserRoleModel,
    SessionModel,
    PasswordResetTokenModel,
    EmailVerificationTokenModel,
)
from app.core.security import hash_password, verify_password, generate_secure_token, hash_token
from app.schemas.auth import RegisterRequest, UserResponse, SessionResponse
from app.services.email_provider import email_provider

SESSION_DURATION_DAYS = 30
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class AuthService:
    @staticmethod
    async def ensure_roles_exist(db: AsyncSession):
        """Seed default USER and ADMIN roles if not existing."""
        roles_to_create = [
            ("USER", "Standard user role with standard workspace access"),
            ("ADMIN", "Administrative superuser with full system governance permissions"),
        ]
        for name, desc in roles_to_create:
            res = await db.execute(select(RoleModel).where(RoleModel.name == name))
            if not res.scalar_one_or_none():
                db.add(RoleModel(name=name, description=desc))
        await db.commit()

    @staticmethod
    async def register_user(req: RegisterRequest, db: AsyncSession, is_admin: bool = False) -> UserModel:
        await AuthService.ensure_roles_exist(db)

        # Check existing user
        res = await db.execute(select(UserModel).where(UserModel.email == req.email.lower()))
        if res.scalar_one_or_none():
            raise ValueError("An account with this email address already exists.")

        # Hash password with Argon2id
        hashed_pwd = hash_password(req.password)
        user = UserModel(
            email=req.email.lower(),
            password_hash=hashed_pwd,
            full_name=req.fullName,
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        await db.flush()

        # Assign role
        target_role = "ADMIN" if is_admin else "USER"
        role_res = await db.execute(select(RoleModel).where(RoleModel.name == target_role))
        role = role_res.scalar_one()
        db.add(UserRoleModel(user_id=user.id, role_id=role.id))

        # Create email verification token
        raw_verify_token = generate_secure_token()
        hashed_verify_token = hash_token(raw_verify_token)
        verify_entry = EmailVerificationTokenModel(
            user_id=user.id,
            token_hash=hashed_verify_token,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db.add(verify_entry)

        await db.commit()
        await db.refresh(user)

        # Dispatch verification via provider abstraction
        await email_provider.send_verification_email(user.email, raw_verify_token)

        return user

    @staticmethod
    async def login_user(
        email: str,
        password: str,
        device_info: str,
        ip_address: str,
        db: AsyncSession,
    ) -> Tuple[UserModel, str]:
        res = await db.execute(select(UserModel).where(UserModel.email == email.lower()))
        user = res.scalar_one_or_none()

        if not user:
            raise ValueError("Invalid email or password.")

        # Account security lock check
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise ValueError(f"Account locked due to multiple failed attempts. Try again after {user.locked_until.strftime('%H:%M:%S UTC')}.")

        # Argon2id password verification
        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            await db.commit()
            raise ValueError("Invalid email or password.")

        # Reset failed attempts on success
        user.failed_login_attempts = 0
        user.locked_until = None

        # Create new DB-backed session
        raw_session_token = generate_secure_token(64)
        token_hash = hash_token(raw_session_token)
        expires_at = datetime.utcnow() + timedelta(days=SESSION_DURATION_DAYS)

        session = SessionModel(
            user_id=user.id,
            session_token_hash=token_hash,
            device_info=device_info,
            ip_address=ip_address,
            is_active=True,
            expires_at=expires_at,
        )
        db.add(session)
        await db.commit()
        await db.refresh(user)

        return user, raw_session_token

    @staticmethod
    async def get_user_by_session_token(token: str, db: AsyncSession) -> Optional[Tuple[UserModel, SessionModel]]:
        if not token:
            return None
        token_hash = hash_token(token)
        res = await db.execute(
            select(SessionModel).where(
                SessionModel.session_token_hash == token_hash,
                SessionModel.is_active == True,
            )
        )
        session = res.scalar_one_or_none()
        if not session:
            return None

        if session.expires_at < datetime.utcnow():
            session.is_active = False
            await db.commit()
            return None

        # Update last accessed
        session.last_accessed_at = datetime.utcnow()
        await db.commit()

        user_res = await db.execute(select(UserModel).where(UserModel.id == session.user_id))
        user = user_res.scalar_one_or_none()
        if not user or not user.is_active:
            return None

        return user, session

    @staticmethod
    async def logout_session(token: str, db: AsyncSession):
        token_hash = hash_token(token)
        await db.execute(
            update(SessionModel)
            .where(SessionModel.session_token_hash == token_hash)
            .values(is_active=False)
        )
        await db.commit()

    @staticmethod
    async def logout_all_user_sessions(user_id: str, db: AsyncSession):
        await db.execute(
            update(SessionModel)
            .where(SessionModel.user_id == user_id)
            .values(is_active=False)
        )
        await db.commit()

    @staticmethod
    async def request_password_reset(email: str, db: AsyncSession):
        res = await db.execute(select(UserModel).where(UserModel.email == email.lower()))
        user = res.scalar_one_or_none()
        if not user:
            return  # Do not leak email existence

        raw_reset_token = generate_secure_token()
        token_hash = hash_token(raw_reset_token)
        reset_entry = PasswordResetTokenModel(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
        db.add(reset_entry)
        await db.commit()

        await email_provider.send_password_reset_email(user.email, raw_reset_token)

    @staticmethod
    async def reset_password(token: str, new_password: str, db: AsyncSession):
        token_hash = hash_token(token)
        res = await db.execute(
            select(PasswordResetTokenModel).where(
                PasswordResetTokenModel.token_hash == token_hash,
                PasswordResetTokenModel.is_used == False,
            )
        )
        reset_entry = res.scalar_one_or_none()

        if not reset_entry or reset_entry.expires_at < datetime.utcnow():
            raise ValueError("Invalid or expired password reset token.")

        user_res = await db.execute(select(UserModel).where(UserModel.id == reset_entry.user_id))
        user = user_res.scalar_one()

        # Update password hash with Argon2id
        user.password_hash = hash_password(new_password)
        reset_entry.is_used = True

        # Revoke all sessions for security
        await db.execute(
            update(SessionModel)
            .where(SessionModel.user_id == user.id)
            .values(is_active=False)
        )
        await db.commit()

    @staticmethod
    async def verify_email_token(token: str, db: AsyncSession) -> bool:
        token_hash = hash_token(token)
        res = await db.execute(
            select(EmailVerificationTokenModel).where(
                EmailVerificationTokenModel.token_hash == token_hash,
                EmailVerificationTokenModel.is_used == False,
            )
        )
        verify_entry = res.scalar_one_or_none()
        if not verify_entry or verify_entry.expires_at < datetime.utcnow():
            return False

        verify_entry.is_used = True
        user_res = await db.execute(select(UserModel).where(UserModel.id == verify_entry.user_id))
        user = user_res.scalar_one()
        user.is_verified = True
        await db.commit()
        return True

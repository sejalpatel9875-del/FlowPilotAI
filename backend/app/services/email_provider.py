import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("flowpilot.email_provider")


class BaseEmailProvider(ABC):
    @abstractmethod
    async def send_verification_email(self, email: str, token: str) -> bool:
        """Abstract method to send email verification links."""
        pass

    @abstractmethod
    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """Abstract method to send password reset links."""
        pass


class ConsoleLoggerEmailProvider(BaseEmailProvider):
    """
    Default provider abstraction.
    Logs dispatch events securely for local dev / testing.
    Can be replaced in Phase 2 with SendGrid, Resend, or AWS SES.
    """
    async def send_verification_email(self, email: str, token: str) -> bool:
        verification_link = f"http://localhost:3000/verify-email?token={token}"
        logger.info(f"[EMAIL PROVIDER] Verification email dispatched to {email}. Verification Link: {verification_link}")
        return True

    async def send_password_reset_email(self, email: str, token: str) -> bool:
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        logger.info(f"[EMAIL PROVIDER] Password reset email dispatched to {email}. Reset Link: {reset_link}")
        return True


# Global default email provider instance
email_provider: BaseEmailProvider = ConsoleLoggerEmailProvider()

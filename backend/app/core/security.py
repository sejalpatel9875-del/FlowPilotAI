import secrets
import hashlib
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

# Configure Argon2id password hasher per OWASP production guidelines
# Type.ID = Argon2id
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64MB memory
    parallelism=4,
    hash_len=32,
    salt_len=16
)


def hash_password(password: str) -> str:
    """Hashes a plain text password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against an Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError, Exception):
        return False


def generate_secure_token(length: int = 32) -> str:
    """Generates a cryptographically secure random token string."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hashes opaque tokens (sessions, verification tokens) with SHA-256."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

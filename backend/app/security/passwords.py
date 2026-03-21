import hashlib

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _bcrypt_input(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) <= 72:
        return password
    digest = hashlib.sha256(raw).hexdigest()
    return f"sha256:{digest}"


def hash_password(password: str) -> str:
    return _pwd_context.hash(_bcrypt_input(password))


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(_bcrypt_input(password), password_hash)

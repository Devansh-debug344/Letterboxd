from passlib.context import CryptContext
from starlette.concurrency import run_in_threadpool
import secrets, hashlib


pwd_context = CryptContext(schemes=['argon2'], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hash_password: str):
    return pwd_context.verify(plain_password, hash_password)


async def hash_password_async(password: str):
    return await run_in_threadpool(hash_password, password)


async def verify_password_async(plain_password: str, hashed_password: str):
    return await run_in_threadpool(verify_password, plain_password, hashed_password)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
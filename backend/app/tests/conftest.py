import pytest
import redis
from app.config import setting
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.db.redis import close_redis

# Use in-memory SQLite file for tests (async driver)
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _clean_redis_session():
    redis.from_url(setting.REDIS_URL).flushdb()
    yield


@pytest.fixture
async def db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def clear_redis():
    r = redis.from_url(setting.REDIS_URL)
    r.flushdb()
    yield
    r.flushdb()


@pytest.fixture
async def client(db):
    app = create_app()

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    await close_redis()


@pytest.fixture
async def test_user(db):
    from app.crud.user import create_user
    from app.schemas.user import CreateUser

    user_data = CreateUser(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )
    return await create_user(user_data, db)
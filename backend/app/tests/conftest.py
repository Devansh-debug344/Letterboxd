import pytest , redis
from app.config import setting
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# def override_get_db():
#     try:
#         db = TestingSessionLocal()
#         yield db
#     finally:
#         db.close()

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def clear_redis():
    """Clear Redis before each test"""
    r = redis.from_url(setting.REDIS_URL)
    r.flushdb()  # Clear all keys
    yield
    r.flushdb()  # Clear after test too

# route needs db
# FastAPI sees get_db in the dict
# value is lambda: db
# calls that lambda
# lambda returns db
#
@pytest.fixture
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda : db #lamda : db is equivalent to any ->  def any(): return db

#     {
#     get_db: lambda: db
# }
    # replacements[real_function] = fake_function
    
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def test_user(db):
    from app.crud.user import create_user
    from app.schemas.user import CreateUser
    
    user_data = CreateUser(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    return create_user(user_data, db)
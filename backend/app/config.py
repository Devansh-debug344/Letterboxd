from dotenv import load_dotenv
import os
from pathlib import Path
grandparent_dir = Path(__file__).resolve().parents[2]

env_path = grandparent_dir / '.env'

load_dotenv(dotenv_path=env_path)
from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    tmdb_api_key : str = os.getenv("TMDB_API_KEY")
    db_url : str = os.getenv("DB_URL")
    JWT_SECRET_TOKEN : str = os.getenv("JWT_SECRET_TOKEN")
    REDIS_URL : str = os.getenv("REDIS_URL")
    REFRESH_TOKEN_EXPIRE_DAYS : int = 7
    TWILIO_API_KEY: str = os.getenv("TWILIO_API_KEY")
    TWILIO_ACCOUNT_SID: str =  os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_API_SECRET : str = os.getenv("TWILIO_API_SECRET")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER")
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    CLOUDINARY_FOLDER: str = os.getenv("CLOUDINARY_FOLDER", "letterboxd")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "")
    # Keep these below the idle timeout of any NAT/load balancer in front of
    # Redis. They are intentionally bounded so a Redis outage cannot hold a
    # web request indefinitely.
    REDIS_SOCKET_CONNECT_TIMEOUT: float = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "2"))
    REDIS_SOCKET_TIMEOUT: float = float(os.getenv("REDIS_SOCKET_TIMEOUT", "2"))
    REDIS_HEALTH_CHECK_INTERVAL: float = float(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))

    # class Config:
    #     env_file = ".env"

setting = Setting()


# @dataclass
# class Setting:
#     app_name : str | None
#     db_url : str 

#     @classmethod
#     def set_env(cls) -> "Setting":
#         app_name = os.getenv("app_name" , "Letterboxd")
#         db_url   = os.getenv("db_url")

#         if not db_url:
#             raise ValueError("DB url is not set in .env")
#         print(db_url , app_name)
#         return cls(
#            app_name =app_name,
#            db_url   = db_url
#         )


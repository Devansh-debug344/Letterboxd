from dotenv import load_dotenv
import os
load_dotenv()
from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    tmdb_api_key : str = os.getenv("tmdb_api_key")
    db_url : str = os.getenv("db_url")
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



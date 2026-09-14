from dotenv import load_dotenv
import os
from dataclasses import dataclass
load_dotenv()


from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    app_name : str = "Movie Booking App"
    jwt_secret : str = "mysecretKey"
    omdb_api_key : str = os.getenv("omdb_api_key")
    db_url : str = os.getenv("db_url")
    SECRET_KEY : str = "3b023ad07e0933837077120184c2b24c6aee1551664742cce96aa537c0333b3d"
    REDIS_URL : str = os.getenv("REDIS_URL")
    REFRESH_TOKEN_EXPIRE_DAYS : int = 7
    TWILIO_API_KEY: str = os.getenv("TWILIO_API_KEY")
    TWILIO_ACCOUNT_SID: str =  os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_API_SECRET : str = os.getenv("TWILIO_API_SECRET")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER")
    class Config:
        env_file = ".env"
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



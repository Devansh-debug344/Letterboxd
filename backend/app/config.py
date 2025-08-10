from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    app_name : str = "Movie Booking App"
    jwt_secret : str = "mysecretKey"
    db_url : str = 'postgresql://postgres:1234@localhost/bookingappdb'
    SECRET_KEY : str = "3b023ad07e0933837077120184c2b24c6aee1551664742cce96aa537c0333b3d"
    class Config:
        env_file = ".env"
setting = Setting()
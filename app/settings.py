from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = {"env_file": ".env"}
    database_url: str = Field(default="sqlite:///app/database/database.db")
    admin_username: str = Field(default="CHANGEME")
    admin_password: str = Field(default="CHANGEME")
    algorithm: str = Field(default="CHANGEME")
    secret_key: str = Field(default="CHANGEME")

settings = Settings()

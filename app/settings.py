from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = {"env_file": ".env"}
    database_url: str = Field(default="sqlite:///test.db")
    admin_username: str = Field(default="ADMIN")
    admin_password: str = Field(default="ADMIN")
    algorithm: str = Field(default="HS256")
    secret_key: str = Field(default="CHANGEME")


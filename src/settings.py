from pydantic import Field
from pydantic_settings import BaseSettings

import os


class CommonSettings(BaseSettings):

    SUPABASE_URL: str = Field(..., env='SUPABASE_URL')
    SUPABASE_KEY: str = Field(..., env='SUPABASE_KEY')
    OPENAI_API_KEY: str = Field(..., env='OPENAI_API_KEY')
    INSTANTLY_API_KEY: str = Field(..., env='INSTANTLY_API_KEY')

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = CommonSettings()
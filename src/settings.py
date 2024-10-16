from pydantic import Field
from pydantic_settings import BaseSettings


class CommonSettings(BaseSettings):
    PROJECT_NAME: str = 'Instantly Analytics'
    PROJECT_DESCRIPTION: str = 'Webhook and API for Instantly for generating weekly and daily reports'
    VERSION: str =  '1.0.0'

    SUPABASE_URL: str = Field(..., env='SUPABASE_URL')
    SUPABASE_KEY: str = Field(..., env='SUPABASE_KEY')
    OPENAI_API_KEY: str = Field(..., env='OPENAI_API_KEY')
    INSTANTLY_API_KEY: str = Field(..., env='INSTANTLY_API_KEY')
    REDIS_HOST: str = Field(..., env='REDIS_HOST')
    REDIS_PORT: str = Field(..., env='REDIS_PORT')
    REDIS_PASSWORD: str = Field(..., env='REDIS_PASSWORD')

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = CommonSettings()
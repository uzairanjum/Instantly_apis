from pydantic import Field
from pydantic_settings import BaseSettings


class CommonSettings(BaseSettings):
    PROJECT_NAME: str = 'Instantly Analytics'
    PROJECT_DESCRIPTION: str = 'Webhook and API for Instantly for generating weekly and daily reports'
    VERSION: str =  '1.0.0'

    SUPABASE_URL: str = Field(..., env='SUPABASE_URL')
    SUPABASE_KEY: str = Field(..., env='SUPABASE_KEY')
    OPENAI_API_KEY: str = Field(..., env='OPENAI_API_KEY')
    REDIS_HOST: str = Field(..., env='REDIS_HOST')
    REDIS_PORT: str = Field(..., env='REDIS_PORT')
    REDIS_PASSWORD: str = Field(..., env='REDIS_PASSWORD')
    GOOGLE_CREDENTIALS: str = Field(..., env='GOOGLE_CREDENTIALS')
    JUSTCALL_API_KEY: str = Field(..., env='JUSTCALL_API_KEY')
    JUSTCALL_API_SECRET: str = Field(..., env='JUSTCALL_API_SECRET')
    PACKBACK_API_KEY: str = Field(..., env='PACKBACK_API_KEY')
    MONGODB_URI: str = Field(..., env='MONGODB_URI')
    

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = CommonSettings()
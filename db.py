from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import create_engine
class Settings(BaseSettings):
    pg_user: str
    pg_password: str
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_db: str = "faculty"

    def get_async_db_url(self):
        return "postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}".format(
            user=self.pg_user,
            password=self.pg_password,
            host=self.pg_host,
            port=self.pg_port,
            db=self.pg_db)
    def get_db_url(self):
        return "postgresql://{user}:{password}@{host}:{port}/{db}".format(
            user=self.pg_user,
            password=self.pg_password,
            host=self.pg_host,
            port=self.pg_port,
            db=self.pg_db)

    model_config = SettingsConfigDict(extra="ignore", env_file=".env")


settings = Settings()

sync_engine = create_engine(settings.get_db_url())
async_engine = create_async_engine(settings.get_async_db_url())

SessionLocal = async_sessionmaker(async_engine,expire_on_commit=False)

async def get_session():
    async with SessionLocal() as session:
        yield session

"""Настройки для установки соединений"""
from typing import AsyncGenerator

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy import create_engine, Engine


class Settings(BaseSettings):
    """Настройки подключения"""
    pg_user: str
    pg_password: str
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_db: str = "faculty"

    def get_async_db_url(self):
        """Возвращает ссылку для асинхронного взаимодействия с БД"""
        return "postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}".format(
            user=self.pg_user,
            password=self.pg_password,
            host=self.pg_host,
            port=self.pg_port,
            db=self.pg_db)

    def get_db_url(self):
        """Возвращает ссылку для инициализации БД"""
        return "postgresql://{user}:{password}@{host}:{port}/{db}".format(
            user=self.pg_user,
            password=self.pg_password,
            host=self.pg_host,
            port=self.pg_port,
            db=self.pg_db)

    model_config = SettingsConfigDict(extra="ignore", env_file=".env")


settings = Settings()


def get_sync_engine():
    return create_engine(settings.get_db_url())


# def get_async_engine():
#     return create_async_engine(settings.get_async_db_url())
# def get_async_sessionmaker():
#     return async_sessionmaker(get_async_engine(), expire_on_commit=False)
#
# async def get_session():
#     async_session = get_async_sessionmaker()
#     async with async_session() as session:
#         yield session


sync_engine: Engine = create_engine(settings.get_db_url(), echo=False)
async_engine: AsyncEngine = create_async_engine(settings.get_async_db_url(), echo=False, pool_size=20, max_overflow=10)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

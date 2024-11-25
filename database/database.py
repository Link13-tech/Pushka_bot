import os
from contextlib import asynccontextmanager
from typing import Union, Callable

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine, AsyncConnection, async_sessionmaker
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


class InternalError(Exception):
    pass


# Функция для получения асинхронной сессии
@asynccontextmanager
async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e


# Функция для создания фабрики сессий
def create_sessionmaker(
    bind_engine: Union[AsyncEngine, AsyncConnection]
) -> Callable[..., async_sessionmaker]:
    return async_sessionmaker(
        bind=bind_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


# Создаем движок
engine = create_async_engine(DATABASE_URL, future=True, echo=True)

# Создаем асинхронную фабрику сессий
async_session = create_sessionmaker(engine)

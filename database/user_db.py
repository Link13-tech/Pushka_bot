from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, UserPoem


# Асинхронная функция для получения или создания пользователя
async def get_or_create_user(db: AsyncSession, telegram_id: int, username: str = None):
    result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
    user = result.scalars().first()

    if not user:
        user = User(telegram_id=telegram_id, username=username)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


# Асинхронная функция для обновления текущего стихотворения
async def update_current_poem_id(session: AsyncSession, telegram_id: int, poem_id: int):
    try:
        result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
        user = result.scalars().first()

        if user:
            user.current_poem_id = poem_id
            await session.commit()
        else:
            print(f"[ERROR] Пользователь с telegram_id={telegram_id} не найден!")
    except SQLAlchemyError as e:
        await session.rollback()
        print(f"[ERROR] Ошибка обновления current_poem_id для telegram_id={telegram_id}: {e}")


# Асинхронная функция для обновления уровня
async def update_current_level(session: AsyncSession, telegram_id: int, level: int):
    try:
        result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
        user = result.scalars().first()

        if user:
            user.current_level = level
            await session.commit()
        else:
            print(f"[ERROR] Пользователь с telegram_id={telegram_id} не найден!")
    except SQLAlchemyError as e:
        await session.rollback()
        print(f"[ERROR] Ошибка обновления current_level для telegram_id={telegram_id}: {e}")


# Асинхронная функция для добавления или обновления результата по стихотворению
async def upsert_user_poem_result(db: AsyncSession, telegram_id: int, poem_id: int, status: str = 'in_progress'):
    user = await get_or_create_user(db, telegram_id)

    result = await db.execute(select(UserPoem).filter(UserPoem.user_id == user.id, UserPoem.poem_id == poem_id))
    user_poem = result.scalars().first()

    if user_poem:
        user_poem.status = status
    else:
        user_poem = UserPoem(user_id=user.id, poem_id=poem_id, status=status)
        db.add(user_poem)

    await db.commit()
    await db.refresh(user_poem)

    return user_poem


# Асинхронная функция для получения статуса стихотворения для пользователя
async def get_user_poem_status(session: AsyncSession, telegram_id: int, poem_id: int):
    try:
        # Получаем пользователя по telegram_id
        result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
        user = result.scalars().first()

        if not user:
            print(f"[ERROR] Пользователь с telegram_id={telegram_id} не найден!")
            return None

        # Проверяем статус стихотворения для данного пользователя
        result = await session.execute(
            select(UserPoem).filter(UserPoem.user_id == user.id, UserPoem.poem_id == poem_id)
        )
        user_poem = result.scalars().first()

        return user_poem.status if user_poem else None
    except SQLAlchemyError as e:
        print(f"[ERROR] Ошибка при получении статуса стихотворения для telegram_id={telegram_id}: {e}")
        return None

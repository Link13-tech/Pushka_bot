from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import text
from database.database import get_async_session

router = Router()


@router.message(Command("poems"))
async def list_poems(message: Message):
    """
    Хендлер для команды /poems — список стихотворений
    """
    async with get_async_session() as session:
        # Оборачиваем запрос в text()
        poems = await session.execute(text("SELECT id, title FROM poems"))
        poems_list = poems.fetchall()
        if poems_list:
            response = "\n".join([f"{poem[0]}. {poem[1]}" for poem in poems_list])
            await message.answer(f"Выберите стихотворение:\n\n{response}")
        else:
            await message.answer("В базе данных пока нет стихотворений.")


@router.message(Command("random"))
async def random_poem(message: Message):
    """
    Хендлер для команды /random — случайное стихотворение
    """
    async with get_async_session() as session:
        poem = await session.execute(text("SELECT id, title, content FROM poems ORDER BY random() LIMIT 1"))
        result = poem.mappings().fetchone()  # Получаем результат как словарь
        if result:
            await message.answer(f"Случайный стих:\n\n{result['content']}")
        else:
            await message.answer("В базе данных пока нет стихотворений.")

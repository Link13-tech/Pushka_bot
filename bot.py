import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram import types, F
from dotenv import load_dotenv
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.poems import router as poems_router
from handlers.share import router as share_router
from handlers.voice import router as voice_router
from handlers.cancel import router as cancel_router
from handlers.feedback import router as feedback_router
import os

# Загружаем переменные окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Токен бота не найден. Убедитесь, что он есть в файле .env")

# Создаем бота и диспетчер
bot = Bot(
    token=BOT_TOKEN,
    session=AiohttpSession(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(cancel_router)
dp.include_router(admin_router)
dp.include_router(feedback_router)
dp.include_router(start_router)
dp.include_router(poems_router)
dp.include_router(share_router)
dp.include_router(voice_router)


@dp.message(F.text.lower() == "/description")
async def description_command(message: types.Message):
    """
    Описание бота.
    """

    await message.answer(
        (
            "Предлагаю вместе окунуться в удивительный мир поэзии, где стихи оживают и запоминаются легко и увлекательно. "
            "Давай пробежимся по основным нюансам взаимодействия со мной.\n\n"
            "1️⃣ <b>Выбор стихотворения:</b>\n"
            "Ты можешь выбрать любимое стихотворение или я с удовольствием предложу тебе вариант случайным образом.\n\n"
            "2️⃣ <b>Уровни сложности:</b>\n"
            "После выбора тебя ждут несколько уровней сложности, каждый из которых поможет тебе освоить стих постепенно. "
            "С каждым следующим уровнем я буду убирать из слов всё больше букв, помогая тебе тренировать память.\n\n"
            "3️⃣ <b>Запись голоса:</b>\n"
            "Чтобы проверить, как ты запомнил текст, ты сможешь записать свой голос на каждом уровне. Это не только полезно для закрепления, "
            "но и приятно – услышать, как красиво звучит стих в твоём исполнении!\n\n"
            "✨ Начинай прямо сейчас! Вперёд, к новым вершинам поэзии! 📖✨- команда в меню☺"
        ),
    )


@dp.message(F.text.lower() == "/contact")
async def contact_command(message: types.Message):
    """
    Контакты для связи.
    """
    await message.answer(
        "Если у вас возникли вопросы, вы можете связаться с нами:\n"
        "📧 E-mail: \n"
        "📞 Телефон:"
    )


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

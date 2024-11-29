import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.enums import ParseMode
from aiogram import types, F
from dotenv import load_dotenv
from handlers.start import router as start_router
from handlers.poems import router as poems_router
from handlers.share import router as share_router
from handlers.voice import router as voice_router
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
dp.include_router(start_router)
dp.include_router(poems_router)
dp.include_router(share_router)
dp.include_router(voice_router)


async def set_bot_commands() -> None:
    """
    Устанавливаем команды для меню бота.
    """
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="description", description="Описание бота"),
        BotCommand(command="contact", description="Контакты для связи"),
    ]
    await bot.set_my_commands(commands)


@dp.message(F.text.lower() == "/description")
async def description_command(message: types.Message):
    """
    Описание бота.
    """
    await message.answer(
        "Это бот для работы со стихами. Здесь вы можете тренировать память, записывать голос и делиться своими успехами."
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
    await set_bot_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

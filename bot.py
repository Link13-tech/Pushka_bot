import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from handlers.start import router as start_router
from handlers.poems import router as poems_router
from handlers.training import router as training_router
import os

# Загружаем переменные окружения
load_dotenv()

# # Настройка логирования
# logging.basicConfig(level=logging.INFO, stream=sys.stdout)

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
dp.include_router(training_router)


async def set_bot_commands() -> None:
    """
    Устанавливаем команды для бота
    """
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="poems", description="Список стихотворений"),
        BotCommand(command="random", description="Случайное стихотворение"),
        BotCommand(command="train", description="Изучать стихотворение"),
    ]
    await bot.set_my_commands(commands)


async def on_startup() -> None:
    """
    Действия при запуске бота
    """
    logging.info("Запуск бота...")
    await set_bot_commands()


async def on_shutdown() -> None:
    """
    Действия при завершении работы бота
    """
    logging.info("Завершение работы бота...")
    await bot.session.close()


async def main() -> None:
    """
    Основная функция запуска бота
    """
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

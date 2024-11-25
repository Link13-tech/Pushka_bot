from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Хендлер для команды /start
    """
    await message.answer(f"Привет, {hbold(message.from_user.full_name)}! Я помогу тебе изучать стихи А.С. Пушкина.")

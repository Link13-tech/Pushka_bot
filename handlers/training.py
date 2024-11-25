from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("train"))
async def start_training(message: Message):
    """
    Хендлер для команды /train — начало обучения
    """
    await message.reply(
        "Выберите уровень сложности:\n"
        "1. С одной пропущенной буквой\n"
        "2. С двумя пропущенными буквами\n"
        "3. Только первая и последняя буквы\n"
        "4. Только первая буква\n\n"
        "Введите номер уровня."
    )

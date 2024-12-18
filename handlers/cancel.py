from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command


router = Router()


@router.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Отменяем процесс ввода и сбрасываем состояние.
    """
    await state.clear()
    await message.reply("Процесс был отменен. Вы можете начать с другой команды.")

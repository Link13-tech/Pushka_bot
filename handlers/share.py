from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(lambda c: c.data == "share_poem")
async def share_poem_handler(callback: CallbackQuery):
    """
    Хендлер для кнопки "Не буду учить, хочу поделиться с друзьями".
    """
    await callback.message.answer("Вы можете поделиться этим стихотворением с друзьями через любой мессенджер или социальную сеть!")

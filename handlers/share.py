from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router
from sqlalchemy import text
from database.database import get_async_session
from database.user_db import get_user_poem_status

# Создаем роутер для обработчика
router = Router()


@router.callback_query(lambda query: query.data.startswith("share_poem") or query.data == "share")
async def finished_or_share_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    user_id = callback.from_user.id
    if callback.data.startswith("share_poem"):
        data = await state.get_data()
        title = data.get("title")

        # Сообщение и кнопки для "Поделиться"
        share_message = (
            f'Я только что выучил(а) стих:  {title}.\n'
            f"Присоединяйтесь к нашему боту, чтобы изучать \nстихи А.С. Пушкина: https://t.me/PushkaRGB_bot"
        )
        vk_share_link = f"https://vk.com/share.php?url=https://t.me/PushkaRGB_bot&title={share_message}"
        ok_share_link = f"https://connect.ok.ru/offer?url=https://t.me/PushkaRGB_bot&title={share_message}"

        share_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Поделиться через VK", url=vk_share_link)],
                [InlineKeyboardButton(text="Поделиться через Одноклассники", url=ok_share_link)],
                [InlineKeyboardButton(text="Я уже поделился? Жми сюда", callback_data="share_done")]
            ]
        )

        # Отправляем сообщение с кнопками для соцсетей
        await callback.message.answer(
            text=share_message,
            reply_markup=share_keyboard
        )

    elif callback.data == "share":
        data = await state.get_data()
        poem_id = data.get('poem_id')
        title = data.get("title")
        async with get_async_session() as session:
            # Проверяем статус стихотворения для пользователя
            poem_status = await get_user_poem_status(session, user_id, poem_id)

            if poem_status == "finished":
                query = text("SELECT title FROM poems WHERE id = :id")
                poem = await session.execute(query, {"id": poem_id})
                result = poem.fetchone()

                if not result:
                    await callback.message.answer("Стихотворение не найдено.")
                    return

                # Сообщение и кнопки для "Поделиться"
                share_message = (
                    f'Я выучил(а) стих:  {title}.\n'
                    f"Присоединяйтесь к нашему боту, чтобы изучать \nстихи А.С. Пушкина: https://t.me/PushkaRGB_bot"
                )
                vk_share_link = f"https://vk.com/share.php?url=https://t.me/PushkaRGB_bot&title={share_message}"
                ok_share_link = f"https://connect.ok.ru/offer?url=https://t.me/PushkaRGB_bot&title={share_message}"

                share_keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Поделиться через VK", url=vk_share_link)],
                        [InlineKeyboardButton(text="Поделиться через Одноклассники", url=ok_share_link)],
                        [InlineKeyboardButton(text="Я уже поделился? Жми сюда", callback_data="share_done")]
                    ]
                )

                await callback.message.answer(text=share_message, reply_markup=share_keyboard)
            else:
                await callback.message.answer(
                    text="Этот стих еще не выучен. Завершите его изучение, чтобы поделиться!",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[[InlineKeyboardButton(text="Выбрать стихотворение", callback_data="start_study")]]
                    )
                )


# Хендлер для кнопок дележа через VK или Одноклассники
@router.callback_query(lambda query: query.data.startswith("share_done"))
async def share_handler(callback: CallbackQuery):

    # Кнопка для выбора следующего стихотворения
    share_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выбрать другое стихотворение", callback_data="start_study")]
        ]
    )

    await callback.message.edit_text(
        text="Спасибо за то, что поделились! Теперь вы можете выбрать следующее стихотворение.",
        reply_markup=share_keyboard
    )

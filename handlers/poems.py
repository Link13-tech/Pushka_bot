from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.database import get_async_session
from sqlalchemy import text
from levels.training_levels import apply_difficulty_level
from database.user_db import upsert_user_poem_result, update_current_poem_id, update_current_level

router = Router()


# Вспомогательная функция для извлечения ID из callback.data
def extract_poem_id(callback_data: str) -> int:
    return int(callback_data.split("_")[1])


# Хендлер для поиска стихов по алфавиту
@router.callback_query(lambda c: c.data == "search_alphabet")
async def search_alphabet_handler(callback: CallbackQuery):
    async with get_async_session() as session:
        query = text("SELECT id, title FROM poems ORDER BY title ASC")
        poems = await session.execute(query)
        poems_list = poems.fetchall()

        if poems_list:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=poem[1], callback_data=f"poem_{poem[0]}")] for poem in poems_list]
            )
            await callback.message.answer("Выберите стихотворение:", reply_markup=keyboard)
        else:
            await callback.message.answer("В базе данных пока нет стихотворений.")


# Хендлер для выбранного стихотворения из списка по алфавиту
@router.callback_query(lambda c: c.data.startswith("poem_"))
async def poem_selected_handler(callback: CallbackQuery):
    poem_id = extract_poem_id(callback.data)

    async with get_async_session() as session:
        query = text("SELECT title FROM poems WHERE id = :id")
        poem = await session.execute(query, {"id": poem_id})
        result = poem.fetchone()

        if result:
            title = result[0]
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f'''Учить "{title}"''', callback_data=f"train_{poem_id}_0")]
                ]
            )
            # Отправляем сообщение с кнопкой для начала изучения
            await callback.message.answer(f"Отличный выбор! Теперь давай начнем изучение стихотворения <b>{title}</b>.", reply_markup=keyboard)
        else:
            await callback.message.answer("Такое стихотворение не найдено.")


# Хендлер для случайного стихотворения
@router.callback_query(lambda c: c.data == "random_poem")
async def random_poem_handler(callback: CallbackQuery):

    async with get_async_session() as session:
        query = text("SELECT title, id FROM poems ORDER BY RANDOM() LIMIT 1")
        poem = await session.execute(query)
        result = poem.fetchone()

        if result:
            title, poem_id = result
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f'''Учить "{title}"''', callback_data=f"train_{poem_id}_0")],
                    [InlineKeyboardButton(text="Не буду учить, хочу поделиться с друзьями", callback_data="share")]
                ]
            )
            # Отправляем сообщение о выбранном стихотворении
            await callback.message.answer(f"Я подобрал для тебя стихотворение <b>{title}</b>.\nНачнем изучение!", reply_markup=keyboard)
        else:
            await callback.message.answer("В базе данных пока нет стихотворений.")


# Общий обработчик для уровней тренировки
async def handle_training_level(callback: CallbackQuery, level: int):
    poem_id = extract_poem_id(callback.data)
    user_id = callback.from_user.id
    async with get_async_session() as session:
        query = text("SELECT title, content FROM poems WHERE id = :id")
        poem = await session.execute(query, {"id": poem_id})
        result = poem.fetchone()

        if result:
            title, content = result
            modified_content = apply_difficulty_level(content, level)
            next_level = level + 1

            # При первом уровне добавляем стихотворение в UserPoem и обновляем текущие данные
            if level == 0:
                await update_current_poem_id(session, user_id, poem_id)
                await update_current_level(session, user_id, level)
                await upsert_user_poem_result(session, user_id, poem_id, status='in_progress')

            # Обновляем уровень на следующем шаге
            if level > 0:
                await update_current_level(session, user_id, level)

            buttons = []
            if level < 4:
                buttons.append([InlineKeyboardButton(text="Записать голос", callback_data=f"record_{poem_id}_{next_level}")])
                buttons.append([InlineKeyboardButton(text="Перейти на следующий уровень", callback_data=f"train_{poem_id}_{next_level}")])
            else:
                buttons.append([InlineKeyboardButton(text="Я выучил!", callback_data=f"finished_{poem_id}")])

            if buttons:
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                await callback.message.answer(f"📜 <b>{title}</b>\n\n{modified_content}", reply_markup=keyboard)
            else:
                await callback.message.answer(f"📜 <b>{title}</b>\n\n{modified_content}")
        else:
            await callback.message.answer("Такое стихотворение не найдено.")


# Универсальный хендлер для всех уровней тренировки
@router.callback_query(lambda c: c.data.startswith("train_"))
async def training_handler(callback: CallbackQuery):
    level = int(callback.data.split("_")[2])
    await handle_training_level(callback, level)


# Хендлер для завершения обучения
@router.callback_query(lambda c: c.data.startswith("finished_"))
async def finished_handler(callback: CallbackQuery):
    poem_id = extract_poem_id(callback.data)
    user_id = callback.from_user.id

    async with get_async_session() as session:
        query = text("SELECT title FROM poems WHERE id = :id")
        poem = await session.execute(query, {"id": poem_id})
        result = poem.fetchone()

        if result:
            title = result[0]
            # Сообщаем о завершении
            await callback.message.answer(f"Поздравляю! Вы выучили стихотворение: {title}")

            # Завершаем обучение для пользователя через User-DB
            await upsert_user_poem_result(session, user_id, poem_id, status='finished')

            # Обнуляем текущий уровень и текущий стих
            await update_current_poem_id(session, user_id, None)
            await update_current_level(session, user_id, 0)
        else:
            await callback.message.answer("Такое стихотворение не найдено.")

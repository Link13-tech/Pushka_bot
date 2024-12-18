from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto

from database import user_db
from database.database import get_async_session
from sqlalchemy import text
from levels.training_levels import apply_difficulty_level
from database.user_db import upsert_user_poem_result, update_current_poem_id, update_current_level


router = Router()


# Вспомогательная функция для извлечения ID из callback.data
def extract_poem_id(callback_data: str) -> int:
    return int(callback_data.split("_")[1])


POEMS_PER_PAGE = 10


# Хендлер поиска стихотворения по алфавиту
@router.callback_query(lambda c: c.data.startswith("search_alphabet"))
async def search_alphabet_handler(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    telegram_user_id = callback.from_user.id
    async with get_async_session() as session:
        user = await user_db.get_or_create_user(session, telegram_user_id, callback.from_user.username)
        user_id = user.id

        if callback.data == "search_alphabet":
            await callback.message.delete()

        # Извлекаем номер страницы из callback_data
        page = 1
        if callback.data != "search_alphabet":
            try:
                page = int(callback.data.split("_")[-1])
            except ValueError:
                await callback.answer("Ошибка при обработке страницы.")
                return

        # Получаем общее количество стихов
        count_query = text("SELECT COUNT(*) FROM poems")
        count_result = await session.execute(count_query)
        total_poems = count_result.scalar()

        # Запрос для получения стихов с пагинацией
        query = text("""
            SELECT p.id, p.title,
                   COALESCE(up.status, 'not_started') AS status
            FROM poems p
            LEFT JOIN user_poems up
            ON p.id = up.poem_id AND up.user_id = :user_id
            ORDER BY p.title ASC
            LIMIT :limit OFFSET :offset
        """)
        result = await session.execute(query, {"user_id": user_id, "limit": POEMS_PER_PAGE, "offset": (page - 1) * POEMS_PER_PAGE})
        poems_list = result.fetchall()

        if poems_list:
            # Создание клавиатуры для вывода стихов
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"{poem[1]} ✅" if poem[2] == "finished" else poem[1],
                            callback_data=f"poem_{poem[0]}"
                        )
                    ]
                    for poem in poems_list
                ]
            )

            # Добавление кнопок навигации
            navigation_buttons = []
            if page > 1:
                navigation_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"search_alphabet_{page - 1}"))
            if page * POEMS_PER_PAGE < total_poems:
                navigation_buttons.append(InlineKeyboardButton(text="Далее ➡️", callback_data=f"search_alphabet_{page + 1}"))

            if navigation_buttons:
                keyboard.inline_keyboard.append(navigation_buttons)

            if callback.data == "search_alphabet":
                await callback.message.answer("Выберите стихотворение:", reply_markup=keyboard)
            else:
                await callback.message.edit_text("Выберите стихотворение:", reply_markup=keyboard)
        else:
            await callback.message.answer("В базе данных пока нет стихотворений.")


# Хендлер для выбранного стихотворения из списка по алфавиту
@router.callback_query(lambda c: c.data.startswith("poem_"))
async def poem_selected_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    poem_id = extract_poem_id(callback.data)

    async with get_async_session() as session:
        query = text("SELECT title, image FROM poems WHERE id = :id")
        poem = await session.execute(query, {"id": poem_id})
        result = poem.fetchone()

        if result:
            title, image = result
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=f'''Учить "{title}"''', callback_data=f"train_{poem_id}_0")]]
            )
            # Сохраняем poem_id в состояние FSM
            await state.update_data(poem_id=poem_id, title=title)

            if image:
                image = FSInputFile(image)
                await callback.message.answer_photo(
                    photo=image,
                    caption=f'''Отличный выбор! Теперь давай начнем изучение стихотворения <b>"{title}"</b>.''',
                    reply_markup=keyboard
                )
            else:
                await callback.message.answer(
                    f'''Отличный выбор! Теперь давай начнем изучение стихотворения <b>"{title}"</b>.''',
                    reply_markup=keyboard
                )
        else:
            await callback.message.answer("Такое стихотворение не найдено.")


# Хендлер для случайного стихотворения
@router.callback_query(lambda c: c.data == "random_poem")
async def random_poem_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    async with get_async_session() as session:
        query = text("SELECT title, id, image FROM poems ORDER BY RANDOM() LIMIT 1")
        poem = await session.execute(query)
        result = poem.fetchone()

        if result:
            title, poem_id, image = result
            await state.update_data(poem_id=poem_id, title=title)

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f'''Учить "{title}"''', callback_data=f"train_{poem_id}_0")],
                    [InlineKeyboardButton(text="Уже выучил, хочу поделиться с друзьями", callback_data="share")],
                    [InlineKeyboardButton(text="Выбрать другое стихотворение", callback_data="start_study")]
                ]
            )

            if image:
                image = FSInputFile(image)
                await callback.message.answer_photo(
                    photo=image,
                    caption=f'''Я подобрал для тебя стихотворение <b>"{title}"</b>.\nНачнем изучение!''',
                    reply_markup=keyboard
                )
            else:
                await callback.message.answer(
                    f'''Я подобрал для тебя стихотворение <b>"{title}"</b>.\nНачнем изучение!''',
                    reply_markup=keyboard
                )


# Общий обработчик для уровней тренировки
async def handle_training_level(callback: CallbackQuery, level: int, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    poem_id = extract_poem_id(callback.data)
    user_id = callback.from_user.id
    title = data["title"]

    print(f"ID стихотворения: {poem_id}")
    print(f"Title стихотворения: {title}")

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

            # Обновляем данные в стейте
            await state.update_data(poem_id=poem_id, current_level=level)

            buttons = []
            if level < 4:
                buttons.append([InlineKeyboardButton(text="Записать голос", callback_data=f"record_{poem_id}_{next_level}")])
                buttons.append([InlineKeyboardButton(text="Перейти на следующий уровень", callback_data=f"train_{poem_id}_{next_level}")])
            else:
                buttons.append([InlineKeyboardButton(text="Записать голос", callback_data=f"record_{poem_id}_{level}")])
                buttons.append([InlineKeyboardButton(text="Я выучил(а)!", callback_data=f"finished_{poem_id}")])

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            poem_message = await callback.message.answer(f"📜 <b>{title}</b>\n{modified_content}", reply_markup=keyboard)
            await state.update_data(poem_message_id=poem_message.message_id)
        else:
            await callback.message.answer("Такое стихотворение не найдено.")


# Универсальный хендлер для всех уровней тренировки
@router.callback_query(lambda c: c.data.startswith("train_"))
async def training_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message_ids = state_data.get("message_ids", [])
    if len(message_ids) > 1:
        for message_id in message_ids[:-1]:
            try:
                await callback.message.bot.delete_message(callback.message.chat.id, message_id)
            except Exception as e:
                print(f"Ошибка при удалении старого сообщения: {e}")

    level = int(callback.data.split("_")[2])
    await handle_training_level(callback, level, state)


@router.callback_query(lambda query: query.data.startswith("finished_"))
async def finished_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    # Получаем данные из состояния
    data = await state.get_data()

    # Получаем `poem_id` и `poem_title` из состояния
    poem_id = data.get('poem_id')
    title = data.get("title")

    async with get_async_session() as session:
        # Обновляем статус стихотворения на 'finished'
        await upsert_user_poem_result(session, user_id, poem_id, status='finished')
        await update_current_poem_id(session, user_id, None)
        await update_current_level(session, user_id, 0)

    # Сообщение и кнопки для "Поделиться" и "Выбрать другое стихотворение"
    share_message = (
        f"🌟 Поздравляем! У тебя получилось! Стихотворение <b>{title}</b> выучено.🌟 "
        f"Весь путь от первого слова до полного стиха пройден, и это невероятно круто! 🎉 "
        f"Твоя настойчивость, внимание к деталям и желание учиться – вдохновляют. Теперь стихотворение не просто строки на бумаге, а часть тебя! 📖✨"
        f"Почему бы не поделиться этим с близкими? Они точно оценят твои старания!"
    )

    share_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Поделиться", callback_data="share_poem")],
            [InlineKeyboardButton(text="Выбрать другое стихотворение", callback_data="start_study")]
        ]
    )

    image_path = "media/dialogs/Ты выучил стих.png"
    image = FSInputFile(image_path)

    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=image,
            caption=share_message
        ),
        reply_markup=share_keyboard
    )

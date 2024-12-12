import re

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram import Router
from sqlalchemy import text

from audio.vk.auth import generate_auth_url, exchange_code_for_token
from audio.vk.publish import publish_post
from audio.vk.upload import upload_audio_file_from_yandex, get_upload_url, save_audio_file
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
        level = 4
        title = data.get("title")

        await state.update_data(user_id=user_id, level=level)

        # Сообщение и кнопки для "Поделиться"
        share_message = (
            f'Я только что выучил стих:  {title}.\n'
            f"Присоединяйтесь к нашему боту, чтобы изучать \nстихи А.С. Пушкина: https://t.me/PushkaRGB_bot"
        )
        vk_share_link = f"https://vk.com/share.php?url=https://t.me/PushkaRGB_bot&title={share_message}"
        ok_share_link = f"https://connect.ok.ru/offer?url=https://t.me/PushkaRGB_bot&title={share_message}"

        vk_auth_url = generate_auth_url()

        share_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Поделиться через VK", url=vk_share_link)],
                [InlineKeyboardButton(text="Поделиться через Одноклассники", url=ok_share_link)],
                [InlineKeyboardButton(text="Поделиться в VK с записью голоса", url=vk_auth_url)],
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
                    f'Я выучил стих:  {title}.\n'
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
                        inline_keyboard=[[InlineKeyboardButton(text="Выбрать стихотворение", callback_data="select_poem")]]
                    )
                )


@router.message(lambda message: message.text and message.text.startswith("Получен код авторизации ВКонтакте:"))
async def handle_vk_code(message: Message, state: FSMContext):
    """
    Обрабатывает код авторизации от VK, получает access_token, загружает и публикует голосовую запись.
    """
    try:
        print(f"Получено сообщение: {message.text}")

        # Извлекаем код авторизации из текста сообщения
        match = re.search(r"Получен код авторизации ВКонтакте:\s*([a-zA-Z0-9]+)", message.text)
        if match:
            code = match.group(1)
            print(f"Извлечен код авторизации: {code}")
        else:
            await message.answer("Не удалось извлечь код авторизации.")
            print("Не удалось извлечь код авторизации из сообщения.")
            return

        # Обмениваем код на access_token
        access_token, vk_user_id = exchange_code_for_token(code)
        print(f"Получен access_token: {access_token}, vk_user_id: {vk_user_id}")

        # Получаем данные из состояния
        data = await state.get_data()
        user_id = data.get("user_id")
        poem_id = data.get("poem_id")
        level = data.get("level")
        title = data.get("title")
        bucket_name = "pushka-bot-storage"

        print(f"Данные из состояния: user_id={user_id}, poem_id={poem_id}, level={level}, title={title}")

        # Получаем URL для загрузки файла
        upload_url = get_upload_url(access_token)
        print(f"Получен URL для загрузки: {upload_url}")

        # Загружаем файл из Yandex Object Storage и получаем параметр file
        file_param = upload_audio_file_from_yandex(upload_url, bucket_name, user_id, poem_id, level)
        print(f"Параметр файла для загрузки: {file_param}")

        # Сохраняем файл как голосовое сообщение в VK
        audio_message = save_audio_file(access_token, file_param)
        owner_id = audio_message["owner_id"]
        audio_id = audio_message["id"]
        print(f"Аудиофайл сохранен: owner_id={owner_id}, audio_id={audio_id}")
        print(f"Голосовое сообщение сохранено: {audio_message}")

        attachment = f"audio{owner_id}_{audio_id}"
        print(attachment)

        share_message = (
            f'Я выучил стих:  {title}.\n'
            f"Присоединяйтесь к нашему боту, чтобы изучать \nстихи А.С. Пушкина: https://t.me/PushkaRGB_bot"
        )

        # Публикуем сообщение на стене пользователя VK
        publish_post(owner_id, share_message, attachment, access_token)
        print("Сообщение опубликовано на стене VK")

        # Ответ пользователю
        await message.answer("Ваше голосовое сообщение успешно опубликовано в ВКонтакте!")

    except Exception as e:
        # В случае ошибки
        print(f"Произошла ошибка: {str(e)}")
        await message.answer(f"Произошла ошибка: {str(e)}")


# Хендлер для кнопок дележа через VK или Одноклассники
@router.callback_query(lambda query: query.data.startswith("share_done"))
async def share_handler(callback: CallbackQuery):

    # Кнопка для выбора следующего стихотворения
    share_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выбрать другое стихотворение", callback_data="select_poem")]
        ]
    )

    await callback.message.edit_text(
        text="Спасибо за то, что поделились! Теперь вы можете выбрать следующее стихотворение.",
        reply_markup=share_keyboard
    )

import os

from aiogram import Router, types
from aiogram.types import CallbackQuery, ContentType, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from database.database import get_async_session
from database.voice_ops import get_original_text
from audio.processing import (
    convert_ogg_to_wav,
    reduce_noise,
    recognize_speech_from_audio,
    clean_text, merge_lines, jaccard_similarity_with_fuzzy,
)

router = Router()


class RecordVoiceState(StatesGroup):
    waiting_for_voice = State()


# Обработчик кнопки "Записать голос"
@router.callback_query(lambda c: c.data.startswith("record_"))
async def start_recording(callback: CallbackQuery, state: FSMContext):
    poem_id = int(callback.data.split("_")[1])
    await state.update_data(poem_id=poem_id)
    await state.set_state(RecordVoiceState.waiting_for_voice)
    await callback.message.answer("🎤 Запишите голосовое сообщение с текстом стихотворения.  Не забывай читать стих громко и с чувством!!☺☺")


# Обработчик голосового сообщения
@router.message(RecordVoiceState.waiting_for_voice)
async def process_voice_message(message: types.Message, state: FSMContext):
    if message.content_type != ContentType.VOICE:
        return  # Игнорируем, если сообщение не голосовое

    user_id = message.from_user.id

    # Извлекаем данные из состояния
    state_data = await state.get_data()
    poem_id = state_data["poem_id"]
    level = state_data["current_level"]
    poem_message_id = state_data.get("poem_message_id")

    # Скачиваем голосовое сообщение
    voice_file = await message.bot.get_file(message.voice.file_id)
    ogg_path = f"audio/files/{user_id}_voice.ogg"
    wav_path = f"audio/files/{user_id}_voice.wav"
    clean_wav_path = f"audio/files/{user_id}_voice_clean.wav"
    await message.bot.download_file(voice_file.file_path, ogg_path)

    try:
        # Обработка аудио
        convert_ogg_to_wav(ogg_path, wav_path)
        reduce_noise(wav_path, clean_wav_path)
        recognized_text = recognize_speech_from_audio(clean_wav_path)

        # Получение эталонного текста из базы данных
        async with get_async_session() as session:
            original_text = await get_original_text(session, poem_id)

        # В одну строку
        merged_original_text = merge_lines(original_text)

        # Очищаем эталонный текст
        cleaned_original_text = clean_text(merged_original_text)

        # Сравнение текста
        similarity = jaccard_similarity_with_fuzzy(recognized_text, cleaned_original_text)

        await message.bot.delete_message(message.chat.id, poem_message_id)

        # Добавляем кнопку для перехода на следующий уровень
        next_level = level + 1
        buttons = [
            [InlineKeyboardButton(text="Перейти на следующий уровень", callback_data=f"train_{poem_id}_{next_level}")]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Ответ пользователю с результатами и кнопкой
        await message.answer(
            f"🎙️ Распознанный текст:\n\n{recognized_text}\n\n"
            f"📜 Эталон:\n{original_text}\n\n"
            f"✅ Совпадение: {similarity}%",
            reply_markup=keyboard
        )

    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке аудио: {e}")

    finally:
        # Удаляем временные файлы
        for path in [ogg_path, wav_path, clean_wav_path]:
            if os.path.exists(path):
                os.remove(path)

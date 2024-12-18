from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import types
from commands.commands import setup_commands_for_user
from database import user_db
from database.database import get_async_session, async_session

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    """
    Хендлер для команды /start. Показывает приветственное сообщение и одну кнопку.
    Создает пользователя, если его нет в базе данных.
    """

    # Удаляем кнопки с последних сообщений (если были)
    for message_id in range(message.message_id - 20, message.message_id):
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=message_id,
                reply_markup=None
            )
        except Exception:
            pass

    # Получаем данные пользователя
    telegram_id = message.from_user.id
    username = message.from_user.username

    # Получаем или создаем пользователя в базе данных
    async with get_async_session() as session:
        await user_db.get_or_create_user(session, telegram_id, username)

    await setup_commands_for_user(message.bot, message.chat.id, async_session)

    await message.answer(
        f"Привет, {username}! Добро пожаловать в бот для изучения стихотворений. "
        f"Перед погружением в литературу золотого века не забудь познакомиться с инструкцией, "
        f"которая поможет тебе в изучении стихов. Все полезные команды найдешь в меню ☺"
    )


@router.message(Command("start_study"))
@router.callback_query(lambda c: c.data == "start_study")
async def start_study_handler(event: types.Message | types.CallbackQuery):
    """
    Универсальный хендлер для команды /start_study и кнопки "start_study".
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Искать по алфавиту", callback_data="search_alphabet")],
            [InlineKeyboardButton(text="Случайное стихотворение", callback_data="random_poem")]
        ]
    )

    response_text = (
        "Давай приступим! Можем найти стихотворение по алфавиту или я предложу тебе случайный стих."
    )

    if isinstance(event, types.Message):
        for message_id in range(event.message_id - 20, event.message_id):
            try:
                await event.bot.edit_message_reply_markup(
                    chat_id=event.chat.id,
                    message_id=message_id,
                    reply_markup=None
                )
            except Exception:
                pass

        await event.answer(response_text, reply_markup=keyboard)

    elif isinstance(event, types.CallbackQuery):
        message = event.message

        if message.text:
            await message.edit_text(response_text, reply_markup=keyboard)
        elif message.caption:
            await message.delete()
            await event.message.answer(response_text, reply_markup=keyboard)
        else:
            await message.answer(response_text, reply_markup=keyboard)


@router.message(lambda message: message.content_type != types.ContentType.VOICE)
async def handle_unrecognized_message(message: types.Message):
    """
    Обработчик для всех сообщений, которые не являются голосовыми сообщениями.
    Пропускает голосовые сообщения, чтобы они не блокировались этим обработчиком.
    """
    await message.answer(
        "Пожалуйста, используйте доступные команды или кнопки.",
    )

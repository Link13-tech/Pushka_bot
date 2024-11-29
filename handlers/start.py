from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import types
from database import user_db
from database.database import get_async_session

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    """
    Хендлер для команды /start. Показывает приветственное сообщение и одну кнопку.
    Создает пользователя, если его нет в базе данных.
    """
    # Получаем данные пользователя
    telegram_id = message.from_user.id
    username = message.from_user.username

    # Получаем или создаем пользователя в базе данных
    async with get_async_session() as session:
        await user_db.get_or_create_user(session, telegram_id, username)

    # Кнопка для выбора стихотворения
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Выбрать стихотворение", callback_data="select_poem")
        ]]
    )

    # Отправляем приветственное сообщение
    await message.answer(
        f"Привет, {username}! Добро пожаловать в бот для изучения стихотворений."
        f"Перед погружением в литературу золотого века не забудь познакомиться с инструкцией,"
        f"которая поможет тебе в изучении стихов, все полезные команды найдешь в меню ☺",
        reply_markup=keyboard,
    )


@router.message(lambda message: message.content_type != types.ContentType.VOICE)
async def handle_unrecognized_message(message: types.Message):
    """
    Обработчик для всех сообщений, которые не являются голосовыми сообщениями.
    Пропускает голосовые сообщения, чтобы они не блокировались этим обработчиком.
    """
    await message.answer(
        "Пожалуйста, используйте доступные команды или кнопки.",
    )


@router.callback_query(lambda c: c.data == "select_poem")
async def select_poem_handler(callback: types.CallbackQuery):
    """
    Хендлер для кнопки "Выбрать стихотворение".
    Показывает сообщение с выбором и две кнопки.
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Искать по алфавиту", callback_data="search_alphabet")],
            [InlineKeyboardButton(text="Случайное стихотворение", callback_data="random_poem")]
        ]
    )
    await callback.message.edit_text(
        "Давай приступим! Можем найти стихотворение по алфавиту или я предложу тебе случайный стих.",
        reply_markup=keyboard,
    )

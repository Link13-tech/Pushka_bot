import os
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from database.database import get_async_session
from models import Poem
from models.user import User, UserRole
from models.user_poem import UserPoem
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference, PieChart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, ReplyKeyboardRemove

router = Router()


# Определяем состояния для FSM
class SetRoleState(StatesGroup):
    waiting_for_telegram_id = State()
    waiting_for_role = State()


class StatsState(StatesGroup):
    choose_action = State()


@router.message(Command("setrole"))
async def set_role_command(message: types.Message, state: FSMContext):
    """
    Начинаем процесс запроса ID и роли для изменения.
    """
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()

        if not user or user.role != UserRole.ADMIN:
            await message.reply("У вас нет прав для выполнения этой команды.")
            return

    await message.reply("Пожалуйста, введите Telegram ID пользователя.")
    await state.set_state(SetRoleState.waiting_for_telegram_id)


@router.message(SetRoleState.waiting_for_telegram_id)
async def process_telegram_id(message: types.Message, state: FSMContext):
    """
    Обрабатываем введенный Telegram ID.
    """
    telegram_id = message.text.strip()

    if not telegram_id.isdigit():
        await message.reply("Пожалуйста, введите правильный Telegram ID (цифры).")
        return

    await state.update_data(telegram_id=telegram_id)

    await message.reply("Теперь введите роль пользователя (например, ADMIN, USER).")
    await state.set_state(SetRoleState.waiting_for_role)


@router.message(SetRoleState.waiting_for_role)
async def process_role(message: types.Message, state: FSMContext):
    """
    Обрабатываем введенную роль.
    """
    new_role = message.text.strip().upper()

    # Проверка на существование роли
    if new_role not in UserRole.__members__:
        await message.reply(f"Некорректная роль. Возможные роли: {', '.join(UserRole.__members__.keys())}")
        return

    user_data = await state.get_data()
    telegram_id = user_data['telegram_id']

    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == int(telegram_id)))
        target_user = result.scalar_one_or_none()

        if target_user:
            target_user.role = UserRole[new_role]
            await session.commit()
            await message.reply(f"Роль пользователя с Telegram ID {telegram_id} изменена на {new_role}.")
        else:
            await message.reply(f"Пользователь с Telegram ID {telegram_id} не найден.")

    await state.clear()


@router.message(Command("stats"))
async def stats_command(message: types.Message, state: FSMContext):
    """
    Обработчик команды /stats для сбора статистики.
    """
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()

        if not user or user.role != UserRole.ADMIN:
            await message.reply("У вас нет прав для выполнения этой команды.")
            return

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Показать статистику на экране", callback_data="show_stats")],
            [InlineKeyboardButton(text="Скачать Excel-файл", callback_data="download_excel")]
        ]
    )

    await message.answer("Выберите удобный варант:", reply_markup=inline_keyboard)
    await state.set_state(StatsState.choose_action)


@router.callback_query(StatsState.choose_action)
async def handle_stats_action(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор действия статистики через инлайн кнопки.
    """
    action = callback_query.data

    if action == "show_stats":
        await show_stats_on_screen(callback_query.message)
    elif action == "download_excel":
        await generate_stats_excel(callback_query.message)
    else:
        await callback_query.message.reply("Пожалуйста, выберите одно из предложенных действий.")

    await callback_query.answer()
    await callback_query.message.delete()
    await state.clear()


async def show_stats_on_screen(message: types.Message):
    """
    Показываем статистику на экране.
    """
    async with get_async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))

        poem_counts = await session.execute(
            select(UserPoem.poem_id, func.count(UserPoem.poem_id))
            .group_by(UserPoem.poem_id)
            .order_by(func.count(UserPoem.poem_id).desc())
        )
        popular_poems = poem_counts.all()

        poem_ids = [poem_id for poem_id, _ in popular_poems]
        poems = await session.execute(select(Poem.id, Poem.title).where(Poem.id.in_(poem_ids)))
        poem_titles = {poem.id: poem.title for poem in poems.all()}

    stats_message = f"Общее количество пользователей: <b>{total_users}</b>\n\n"
    stats_message += "Популярные стихотворения:\n"
    stats_message += f"{'Название'.ljust(52)} {'Кол-во'.rjust(6)}\n"
    stats_message += "=" * 58 + "\n"

    for poem_id, count in popular_poems:
        title = poem_titles.get(poem_id, "Неизвестное стихотворение")
        stats_message += f"{title[:50].ljust(52)} {str(count).rjust(6)} пользователей\n"

    await message.answer(stats_message)


async def generate_stats_excel(message: types.Message):
    """
    Генерируем Excel-файл со статистикой и добавляем диаграммы.
    """
    async with get_async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))

        poem_counts = await session.execute(
            select(UserPoem.poem_id, func.count(UserPoem.poem_id))
            .group_by(UserPoem.poem_id)
            .order_by(func.count(UserPoem.poem_id).desc())
        )
        popular_poems = poem_counts.all()

        poem_ids = [poem_id for poem_id, _ in popular_poems]
        poems = await session.execute(select(Poem.id, Poem.title).where(Poem.id.in_(poem_ids)))
        poem_titles = {poem.id: poem.title for poem in poems.all()}

    stats_dir = "stats"
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"stats_{current_time}.xlsx"
    file_path = os.path.join(stats_dir, file_name)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Статистика"

    # Устанавливаем ширину столбцов
    sheet.column_dimensions['A'].width = 236 / 7
    sheet.column_dimensions['B'].width = 180 / 7

    sheet.append([])
    sheet.append(["Общее количество пользователей", total_users])
    sheet.append([])
    sheet.append(["Стихотворение", "Количество пользователей"])

    for poem_id, count in popular_poems:
        poem_title = poem_titles.get(poem_id, f"Неизвестное стихотворение (ID {poem_id})")
        sheet.append([poem_title, count])

    # Добавление столбчатой диаграммы (Bar Chart) на D2
    bar_chart = BarChart()
    data = Reference(sheet, min_col=2, min_row=4, max_col=2, max_row=len(popular_poems) + 3)
    categories = Reference(sheet, min_col=1, min_row=4, max_row=len(popular_poems) + 3)
    bar_chart.add_data(data, titles_from_data=True)
    bar_chart.set_categories(categories)
    bar_chart.title = "Популярность стихотворений"
    bar_chart.x_axis.title = "Стихотворения"
    bar_chart.y_axis.title = "Количество пользователей"

    sheet.add_chart(bar_chart, "D2")

    # Добавление круговой диаграммы (Pie Chart) на D17
    pie_chart = PieChart()
    data_pie = Reference(sheet, min_col=2, min_row=4, max_col=2, max_row=len(popular_poems) + 3)
    labels = Reference(sheet, min_col=1, min_row=4, max_row=len(popular_poems) + 3)
    pie_chart.add_data(data_pie, titles_from_data=True)
    pie_chart.set_categories(labels)
    pie_chart.title = "Распределение популярности стихотворений"

    sheet.add_chart(pie_chart, "D17")

    workbook.save(file_path)

    input_file = FSInputFile(file_path)
    await message.answer_document(input_file, filename=file_name)

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database.database import get_async_session
from models.user import User, UserRole

router = Router()


# Определяем состояния для FSM
class SetRoleState(StatesGroup):
    waiting_for_telegram_id = State()
    waiting_for_role = State()


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

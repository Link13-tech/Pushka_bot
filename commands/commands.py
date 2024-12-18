from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from sqlalchemy import select
from models import User
from models.user import UserRole


async def set_default_commands(bot: Bot):
    """Настройка команд для всех пользователей."""
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="description", description="Описание бота"),
        BotCommand(command="start_study", description="Погружаемся в литературу"),
        BotCommand(command="contact", description="Контакты для связи"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def set_admin_commands(bot: Bot, admin_chat_id: int):
    """Настройка команд для администраторов."""
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="description", description="Описание бота"),
        BotCommand(command="start_study", description="Погружаемся в литературу"),
        BotCommand(command="contact", description="Контакты для связи"),
        BotCommand(command="setrole", description="Изменить роль пользователя"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="cancel", description="Сброс команды/данных")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=admin_chat_id))


async def setup_commands_for_user(bot: Bot, chat_id: int, session_maker):
    """Проверяет роль пользователя и устанавливает команды для него."""
    async with session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == chat_id))
        user = result.scalar_one_or_none()

        if user:
            print(f"User found: {user.telegram_id}, Role: {user.role}, Role type: {type(user.role)}")
            if user.role == UserRole.ADMIN:
                await set_admin_commands(bot, admin_chat_id=chat_id)
                commands = await bot.get_my_commands(scope=BotCommandScopeChat(chat_id=chat_id))
                print(f"Admin commands set for user: {chat_id}, Commands: {commands}")
            else:
                await set_default_commands(bot)
                commands = await bot.get_my_commands(scope=BotCommandScopeChat(chat_id=chat_id))
                print(f"Default commands set for user: {chat_id}, Commands: {commands}")
        else:
            await set_default_commands(bot)

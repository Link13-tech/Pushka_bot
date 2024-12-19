from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database.database import get_async_session
from models.user import User, UserRole

router = Router()


class FeedbackState(StatesGroup):
    waiting_for_feedback = State()


@router.message(Command("feedback"))
async def handle_feedback(message: types.Message, state: FSMContext):
    """
    Обработчик команды /feedback для обычных пользователей и администраторов.
    """
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("Вы не зарегистрированы в системе.")
            return

        if user.role == UserRole.ADMIN:
            inline_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Скачать отзывы", callback_data="download_feedback")],
                    [InlineKeyboardButton(text="Оставить отзыв", callback_data="leave_feedback")]
                ]
            )
            await message.answer("Какое действие вы хотите выполнить?", reply_markup=inline_keyboard)
        else:
            await message.answer("Напишите, пожалуйста, текст вашего отзыва.")
            await state.set_state(FeedbackState.waiting_for_feedback)
            await state.update_data(user_id=user_id, user_name=user_name)


@router.callback_query(lambda call: call.data in ["download_feedback", "leave_feedback"])
async def admin_feedback_action(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик действий администратора при нажатии на кнопки.
    """
    action = callback.data
    print(f"[DEBUG] Администратор выбрал действие: {action}")

    if action == "download_feedback":
        file_path = "feedback.txt"
        try:
            feedback_file = FSInputFile(file_path)
            await callback.message.delete()
            await callback.message.answer_document(feedback_file, caption="Файл с отзывами готов.")
            print(f"[DEBUG] Файл {file_path} успешно отправлен администратору")
        except FileNotFoundError:
            print(f"[DEBUG] Файл {file_path} не найден")
            await callback.message.edit_text("Файл с отзывами пока пуст.")
    elif action == "leave_feedback":
        await callback.message.edit_text("Напишите, пожалуйста, текст вашего отзыва.")
        await state.set_state(FeedbackState.waiting_for_feedback)
        await state.update_data(user_id=callback.from_user.id, user_name=callback.from_user.full_name)
    await callback.answer()


@router.message(FeedbackState.waiting_for_feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    """
    Обрабатываем отзыв от пользователя или администратора.
    """
    user_data = await state.get_data()
    feedback = message.text.strip()

    if feedback:
        print(f"[DEBUG] Отзыв от пользователя {user_data['user_id']}: {feedback}")
        await save_feedback_to_file(user_data['user_id'], user_data['user_name'], feedback)
        await message.answer("Спасибо за ваш отзыв!")
    else:
        await message.answer("Пожалуйста, отправьте текст вашего отзыва.")

    await state.clear()


async def save_feedback_to_file(user_id: int, user_name: str, feedback: str):
    """
    Сохраняем отзыв в файл.
    """
    print(f"[DEBUG] Сохранение отзыва в файл: User ID={user_id}, Name={user_name}, Feedback={feedback}")
    try:
        with open('feedback.txt', 'a', encoding='utf-8') as file:
            file.write(f"User ID: {user_id}, User name: {user_name}, Feedback: {feedback}\n")
        print("[DEBUG] Отзыв успешно сохранен в файл")
    except Exception as e:
        print(f"[ERROR] Ошибка при сохранении отзыва в файл: {e}")

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

def get_start_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Додати витрату", callback_data="add_expense")
    kb.button(text="Отримати звіт", callback_data="get_report")
    kb.button(text="Відредагувати витрату", callback_data="edit_expense")
    kb.button(text="Видалити витрату", callback_data="delete_expense")
    kb.adjust(1, 1, 2)
    return kb.as_markup()

def get_confirm_addition_expense_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Так", callback_data="confirm_addition_expense")
    kb.button(text="Ні", callback_data="cancel_addition_expense")
    return kb.as_markup()

def get_confirm_edition_expense_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Так", callback_data="confirm_edition_expense")
    kb.button(text="Ні", callback_data="cancel_edition_expense")
    return kb.as_markup()

def get_date_kb():
    date = datetime.now().date()
    date = date.strftime("%d.%m.%Y")
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=str(date))]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
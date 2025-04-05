from datetime import datetime
from aiogram.types import InputFile, BufferedInputFile

from aiogram import Router, types
from aiogram.filters import Command

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from keyboards import *
from api_client import *
from utils import generate_expenses_excel, is_valid_date, is_expense_id_valid
from create_bot import bot

router = Router()

@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    user = await get_user(message.chat.id)
    if user is None:
        user = await create_user(
            telegram_id=message.chat.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    username = user.get("username")
    first_name = user.get("first_name")
    last_name = user.get("last_name")
    name = f"{first_name} {last_name}" if first_name and last_name else first_name or last_name or username
    
    msg =await message.answer(f"Вітаю, *{name}*!\n\nЯ бот, який допомагає контролювати витрати.\n\nОбирай дію нижче:", 
        reply_markup=get_start_kb(),
        parse_mode="Markdown"
    )
    await state.update_data(last_msg_id=msg.message_id)

class AddExpense(StatesGroup):
    name = State()
    date = State()
    amount_uah = State()

@router.callback_query(lambda c: c.data == "add_expense")
async def add_expense_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    msg_id = data.get("last_msg_id")

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=msg_id,
        text="Додаємо нову витрату.\n\nВведи назву (наприклад, «Щомісячна сплата за інтернет»):"
    )

    await state.set_state(AddExpense.name)
    
@router.message(AddExpense.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)
    await message.answer(
        f"Витрата «*{name}*»\n\nТепер введи дату витрати (формат: dd.mm.YYYY)\nАбо натисни кнопку, щоб вибрати сьогоднішню дату:",
        parse_mode="Markdown",
        reply_markup=get_date_kb()
        )
    
    await state.set_state(AddExpense.date)
    
@router.message(AddExpense.date)
async def process_date(message: types.Message, state: FSMContext):
    date = message.text
    
    if not await is_valid_date(date):
        await message.answer(
            f"Дата «*{date}*» некоректна.\n\n Спробуй ще раз (формат: dd.mm.YYYY, наприклад, «19.03.2025»):",
            parse_mode="Markdown"
            )
        await state.set_state(AddExpense.date)
        return
    
    await state.update_data(date=date)
    await message.answer(
        f"Витрата за «*{date}*»\n\nТепер введи суму витрати в гривнях:",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
        )
    await state.set_state(AddExpense.amount_uah)

@router.message(AddExpense.amount_uah)
async def process_amount_uah(message: types.Message, state: FSMContext):
    try:
        amount_uah = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(
            f"Сума «*{message.text}*» некоректна.\n\n Спробуй ще раз (тільки цифри):",
            parse_mode="Markdown",
            )
        await state.set_state(AddExpense.amount_uah)
        return

    amount_usd = await convert_uah_to_usd(amount_uah)
    if amount_usd is None:
        await message.answer(
            f"Не вдалося отримати курс долара.\n\n Спробуй ще раз пізніше.",
            parse_mode="Markdown"
            )
        return
    
    await state.update_data(amount_uah=amount_uah)
    await state.update_data(amount_usd=amount_usd)
    
    data = await state.get_data()
    name= data.get("name")
    dete= data.get("date")
    
    await message.answer(f"""
Якщо наступні дані правильні, натисни «Так», щоб створити витрату, або «Ні», щоб скасувати:

Назва: «*{name}*»
Дата: *{dete}*
Сума: *{amount_uah} UAH* (_{amount_usd} USD_)
""",
        reply_markup=get_confirm_addition_expense_kb(),
        parse_mode="Markdown"
        )
    await state.set_state(AddExpense.сonfirm)

@router.callback_query(lambda c: c.data == "confirm_addition_expense")
async def confirm_addition_expense(callback: types.CallbackQuery, state: FSMContext):    
    data = await state.get_data()
    name = data.get("name")
    date = data.get("date")
    amount_uah = data.get("amount_uah")
    amount_usd = data.get("amount_usd")
    
    expense = await create_expense(
        telegram_id=callback.message.chat.id,
        name=name,
        date=date,
        amount_uah=amount_uah,
        amount_usd=amount_usd
    )
    expense_id = expense.get("id")
    
    await callback.answer()
    await callback.message.answer(
        f"Витрату успішно додано!\n\nID витрати: {expense_id}"
    )
    await reset_state(callback.message, state)

@router.callback_query(lambda c: c.data == "cancel_addition_expense")
async def cancel_addition_expense(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Додавання витрати скасовано.")
    await reset_state(callback.message, state)

class GetReport(StatesGroup):
    start_date = State()
    end_date = State()
    
@router.callback_query(lambda c: c.data == "get_report")
async def get_report_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    msg_id = data.get("last_msg_id")

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=msg_id,
        text="Отримуємо звіт.\n\nВведи початкову дату (формат: dd.mm.YYYY):"
    )

    await state.set_state(GetReport.start_date)
    
@router.message(GetReport.start_date)
async def process_start_date(message: types.Message, state: FSMContext):
    start_date = message.text
    
    if not await is_valid_date(start_date):
        await message.answer(
            f"Дата «*{start_date}*» некоректна.\n\n Спробуй ще раз (формат: dd.mm.YYYY, наприклад, «19.03.2025»):",
            parse_mode="Markdown"
            )
        await state.set_state(GetReport.start_date)
        return
    
    await state.update_data(start_date=start_date)
    await message.answer(
        f"Початкова дата «*{start_date}*»\n\nТепер введи кінцеву дату (формат: dd.mm.YYYY):",
        parse_mode="Markdown"
        )
    await state.set_state(GetReport.end_date)

@router.message(GetReport.end_date)
async def process_end_date(message: types.Message, state: FSMContext):
    end_date = message.text
    
    if not await is_valid_date(end_date):
        await message.answer(
            f"Дата «*{end_date}*» некоректна.\n\n Спробуй ще раз (формат: dd.mm.YYYY, наприклад, «19.03.2025»):",
            parse_mode="Markdown"
            )
        await state.set_state(GetReport.end_date)
        return
    
    data = await state.get_data()
    start_date = data.get("start_date")
    
    if start_date > end_date:
        await message.answer(
            f"Кінцева дата «*{end_date}*» повинна бути пізніше початкової дати «*{start_date}*».\n\n Спробуй ще раз:",
            parse_mode="Markdown"
            )
        await state.set_state(GetReport.end_date)
        return
    
    await state.update_data(end_date=end_date)
    
    data = await state.get_data()
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    
    msg = await message.answer('⌛')
    expenses = await get_expenses(
        telegram_id=message.chat.id,
        start_date=start_date,
        end_date=end_date
    )
    if not expenses:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=f"Витрат за період з «*{start_date}*» по «*{end_date}*» не знайдено.",
            parse_mode="Markdown"
            )
    else:
        excel_file = await generate_expenses_excel(expenses)
        file_name = f"{start_date}_{end_date}.xlsx"
        input_file = BufferedInputFile(
            file=excel_file.getvalue(),
            filename=file_name
        )

        await bot.send_document(
            chat_id=message.chat.id,
            document=input_file
        )
        
        total_amount_uah = sum(expense["amount_uah"] for expense in expenses)
        total_amount_usd = sum(expense["amount_usd"] for expense in expenses)
        
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=f"Звіт за *{start_date} - {end_date}* готовий!\n\nЗагальна сума витрат:*\n-{total_amount_uah} UAH\n-{total_amount_usd} USD*\n\n Завантажуй файл:",
            parse_mode="Markdown"
        )
    await reset_state(message, state)

class DeleteExpense(StatesGroup):
    expense_id = State()

@router.callback_query(lambda c: c.data == "delete_expense")
async def delete_expense_handler(callback: types.CallbackQuery, state: FSMContext):
    expenses = await get_expenses(telegram_id=callback.message.chat.id)
    if not expenses:
        await callback.answer("У тебе немає витрат для видалення.")
        return
    
    await callback.answer()
    
    data = await state.get_data()
    msg_id = data.get("last_msg_id")
    
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=msg_id,
        text="⌛",
    )  
    await send_expenses_list(callback.message.chat.id, expenses)    
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=msg_id,
        text=f"Редагування витрати:\n\nВибери ID витрати зі списку, яку треба редагувати:",
    )
    await state.set_state(DeleteExpense.expense_id)

@router.message(DeleteExpense.expense_id)
async def process_expense_id_delete(message: types.Message, state: FSMContext):
    if not await is_expense_id_valid(message.text):
        await message.answer(
            f"ID витрати «*{message.text}*» некоректний.\n\nСпробуй ще раз (тільки цифри):",
            parse_mode="Markdown"
            )
        await state.set_state(DeleteExpense.expense_id)
        return
    expense = await delete_expense(message.text)
    if not expense:
        await message.answer(
            f"Витрати з ID «*{message.text}*» не знайдено.\n\nСпробуй ввести інший айді:",
            parse_mode="Markdown"
            )
        await state.set_state(DeleteExpense.expense_id)
        return
    await message.answer(
        f"Витрату з ID «*{message.text}*» успішно видалено.",
        parse_mode="Markdown"
        )
    await reset_state(message, state)

class EditExpense(StatesGroup):
    expense_id = State()
    name = State()
    date = State()
    amount_uah = State()

@router.callback_query(lambda c: c.data == "edit_expense")
async def edit_expense_handler(callback: types.CallbackQuery, state: FSMContext):
    expenses = await get_expenses(telegram_id=callback.message.chat.id)
    if not expenses:
        await callback.answer("У тебе немає витрат для редагування.")
        return
    
    await callback.answer()
    
    data = await state.get_data()
    msg_id = data.get("last_msg_id")
    
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=msg_id,
        text="⌛",
    )
    await send_expenses_list(callback.message.chat.id, expenses)
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=msg_id,
        text=f"Редагування витрати:\n\nВибери ID витрати зі списку, яку треба редагувати:",
    )
    await state.set_state(EditExpense.expense_id)

@router.message(EditExpense.expense_id)
async def process_expense_id_edit(message: types.Message, state: FSMContext):
    if not await is_expense_id_valid(message.text):
        await message.answer(
            f"ID витрати «*{message.text}*» некоректний.\n\nСпробуй ще раз (тільки цифри):",
            parse_mode="Markdown"
            )
        await state.set_state(EditExpense.expense_id)
        return
    
    expense = await get_expenses(
        telegram_id = message.chat.id,
        expense_id=message.text
    )
    if not expense:
        await message.answer(
            f"Витрати з ID «*{message.text}*» не знайдено.\n\nСпробуй ввести інший айді:",
            parse_mode="Markdown"
            )
        await state.set_state(EditExpense.expense_id)
        return
    
    await state.update_data(expense_id=message.text)
    
    await message.answer(
        f"Витрату з ID «*{message.text}*» знайдено.\n\nВведи нову назву витрати (наприклад, «Щомісячна сплата за інтернет»):",
        parse_mode="Markdown"
    )
    await state.set_state(EditExpense.name)

@router.message(EditExpense.name)
async def process_name_edit(message: types.Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)
    await message.answer(
        f"Витрата «*{name}*»\n\nТепер введи нову дату витрати (формат: dd.mm.YYYY)\nАбо натисни кнопку, щоб вибрати сьогоднішню дату:",
        parse_mode="Markdown",
        reply_markup=get_date_kb()
        )
    
    await state.set_state(EditExpense.date)

@router.message(EditExpense.date)
async def process_date_edit(message: types.Message, state: FSMContext):
    date = message.text
    
    if not await is_valid_date(date):
        await message.answer(
            f"Дата «*{date}*» некоректна.\n\n Спробуй ще раз (формат: dd.mm.YYYY, наприклад, «19.03.2025»):",
            parse_mode="Markdown"
            )
        await state.set_state(EditExpense.date)
        return
    
    await state.update_data(date=date)
    await message.answer(
        f"Витрата за «*{date}*»\n\nТепер введи нову суму витрати в гривнях:",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
        )
    await state.set_state(EditExpense.amount_uah)
    
@router.message(EditExpense.amount_uah)
async def process_amount_uah_edit(message: types.Message, state: FSMContext):
    try:
        amount_uah = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(
            f"Сума «*{message.text}*» некоректна.\n\n Спробуй ще раз (тільки цифри):",
            parse_mode="Markdown"
            )
        await state.set_state(EditExpense.amount_uah)
        return

    amount_usd = await convert_uah_to_usd(amount_uah)
    if amount_usd is None:
        await message.answer(
            f"Не вдалося отримати курс долара.\n\n Спробуй ще раз пізніше.",
            parse_mode="Markdown"
            )
        return
    
    await state.update_data(amount_uah=amount_uah)
    await state.update_data(amount_usd=amount_usd)
    
    data = await state.get_data()
    name = data.get("name")
    date = data.get("date")
    
    await message.answer(f"""
Якщо наступні дані правильні, натисни «Так», щоб зберегти зміни, або «Ні», щоб скасувати:

Назва: «*{name}*»
Дата: *{date}*
Сума: *{amount_uah} UAH* (_{amount_usd} USD_)
""",
        reply_markup=get_confirm_edition_expense_kb(),
        parse_mode="Markdown"
        )

@router.callback_query(lambda c: c.data == "confirm_edition_expense")
async def confirm_edition_expense(callback: types.CallbackQuery, state: FSMContext):    
    data = await state.get_data()
    expense_id = data.get("expense_id")
    name = data.get("name")
    date = data.get("date")
    amount_uah = data.get("amount_uah")
    amount_usd = data.get("amount_usd")
    
    expense = await update_expense(
        telegram_id=callback.message.chat.id,
        expense_id=expense_id,
        name=name,
        date=date,
        amount_uah=amount_uah,
        amount_usd=amount_usd
    )
    
    await callback.answer()
    await callback.message.answer(
        f"Витрату успішно змінено!\n\nID витрати: {expense_id}"
    )
    await reset_state(callback.message, state)

@router.callback_query(lambda c: c.data == "cancel_edition_expense")
async def cancel_edition_expense(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Редагування витрати скасовано.")
    await reset_state(callback.message, state)

async def send_expenses_list(chat_id: int, expenses: list):
    excel_file = await generate_expenses_excel(expenses)
    file_name = f"{chat_id}.xlsx"
    input_file = BufferedInputFile(
        file=excel_file.getvalue(),
        filename=file_name
    )

    await bot.send_document(
        chat_id=chat_id,
        document=input_file
    )     

async def reset_state(message:types.Message, state: FSMContext):
    await state.clear()
    await start_command(message, state)
    
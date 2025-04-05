import pandas as pd
from io import BytesIO
from datetime import datetime
from openpyxl import load_workbook

def convert_date_format(date_str: str) -> str:
    return datetime.strptime(date_str, "%d.%m.%Y").date().isoformat()

async def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False

async def is_expense_id_valid(expense_id: int) -> bool:
    try:
        expense_id = int(expense_id)
        return expense_id > 0
    except ValueError:
        return False

async def generate_expenses_excel(expenses: list) -> BytesIO:
    df = pd.DataFrame(expenses)
    df = df.sort_values(by='id').reset_index(drop=True)

    df.loc[len(df.index)] = {
        'id': '',
        'name': 'Загалом:',
        'date': '',
        'amount_uah': df['amount_uah'].sum(),
        'amount_usd': df['amount_usd'].sum()
    }

    file_stream = BytesIO()
    with pd.ExcelWriter(file_stream, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Витрати')

    file_stream.seek(0)
    wb = load_workbook(file_stream)
    ws = wb.active
    
    final_stream = BytesIO()
    wb.save(final_stream)
    final_stream.seek(0)
    
    return file_stream


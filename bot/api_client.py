import httpx
from config import SERVER_URL
from utils import convert_date_format

async def get_user(telegram_id: int):
    url = f"{SERVER_URL}/users/{telegram_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
        
async def create_user(telegram_id: int, username: str, first_name: str, last_name: str):
    url = f"{SERVER_URL}/users/"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name
        })
        if response.status_code == 200:
            return response.json()
        else:
            return None
        
async def create_expense(telegram_id: int, name: str, date: str, amount_uah: float, amount_usd: float):
    url = f"{SERVER_URL}/expenses/"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={
            "telegram_id": telegram_id,
            "name": name,
            "date": date,
            "amount_uah": amount_uah,
            "amount_usd": amount_usd
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            return None

async def get_expenses(telegram_id: int, start_date: str = None, end_date: str = None, expense_id: int = None):
    url = f"{SERVER_URL}/expenses/"
    
    params = {"telegram_id": telegram_id}

    if start_date:
        start_date = convert_date_format(start_date)
        params["start_date"] = start_date

    if end_date:
        end_date = convert_date_format(end_date)
        params["end_date"] = end_date

    if expense_id is not None:
        params["expense_id"] = expense_id

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return None

async def delete_expense(expense_id: int):
    url = f"{SERVER_URL}/expenses/{expense_id}"
    async with httpx.AsyncClient() as client:
        response = await client.delete(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None

async def update_expense(telegram_id:int, expense_id: int, name: str, date: str, amount_uah: float, amount_usd: float):
    url = f"{SERVER_URL}/expenses/{expense_id}"
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json={
            "telegram_id": telegram_id,
            "name": name,
            "date": date,
            "amount_uah": amount_uah,
            "amount_usd": amount_usd
        })
        if response.status_code == 200:
            return response.json()
        else:
            return None

async def convert_uah_to_usd(amount_uah: float) -> float:
    url = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&json'
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            rate = response.json()[0]['rate']
            return round(amount_uah / rate, 2)
        else:
            return None
        

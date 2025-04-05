# Expense Tracker Bot

Бот на Aiogram + сервер на FastAPI

---

**Структура проєкту:**

- `bot/` — папка з ботом, основний файл `main.py`
- `server/` — FastAPI сервер, основний файл `main.py`
- `bot/.env` — конфіг з токенами та URL

---

**Що має бути в `.env`:**

BOT_TOKEN=(наприклад, 7715213818:AAGw-0wfhRCs73IJ3xxgXvIrx0p1kCazzIE (@TestTaskExpenseControlBot))
ADMIN_ID=(наприклад, 1306364171 (дізнатися можна на https://t.me/FIND_MY_ID_BOT))
SERVER_URL=http://localhost:8000

---

**Як запустити сервер:**

1. Перейти в папку `server`
2. Запустити:
```
uvicorn main:app --reload
```
---

**Як запустити бота:**

1. Перейти в папку `bot`
2. Запустити:
```
python main.py
```
---

**Залежності:**
```
pip install requirements.txt
```

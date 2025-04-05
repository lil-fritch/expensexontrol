import asyncio

from config import  ADMIN_ID
from handlers import router

from create_bot import bot, dp

async def on_startup(bot):
    print("Bot started")
    await bot.send_message(chat_id=ADMIN_ID, text="Bot started")

async def main():    
    dp.include_router(router)
    dp.startup.register(on_startup)    
    
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        print("Bot stopped")
    finally:
        await bot.session.close() 

if __name__ == "__main__":
    asyncio.run(main())
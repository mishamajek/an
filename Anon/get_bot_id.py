import asyncio
import os
from telethon import TelegramClient

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'
BOT_USERNAME = '@MessageAnonBot'
SESSION_NAME = 'sessions/17788323682'  # Используем рабочий аккаунт

async def main():
    # Используем существующий файл сессии
    if not os.path.exists(f"{SESSION_NAME}.session"):
        print(f"❌ Файл сессии не найден: {SESSION_NAME}.session")
        print("Проверьте, что файл существует в папке sessions/")
        return
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()
    
    try:
        bot = await client.get_entity(BOT_USERNAME)
        print(f"✅ Бот найден!")
        print(f"   ID: {bot.id}")
        print(f"   Username: {bot.username}")
        print(f"   Access Hash: {bot.access_hash}")
        
        # Сохраняем ID для использования
        with open('bot_id.txt', 'w') as f:
            f.write(str(bot.id))
        print("\n✅ ID сохранен в bot_id.txt")
        
        # Проверяем, что можем отправить сообщение
        await client.send_message(bot, '/start')
        print("✅ Отправлен /start")
        
        # Ждем ответ
        await asyncio.sleep(2)
        
        # Получаем последнее сообщение от бота
        async for msg in client.iter_messages(bot, limit=1):
            if msg.text:
                print(f"📩 Ответ бота: {msg.text[:200]}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
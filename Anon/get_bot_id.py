import asyncio
import os
from telethon import TelegramClient

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'
BOT_USERNAME = '@MessageAnonBot'

# Используем рабочий аккаунт (тот, который уже отправлял сообщения)
SESSION_NAME = 'sessions/user_17788323682'

async def main():
    # Проверяем, существует ли файл
    if not os.path.exists(f"{SESSION_NAME}.session"):
        print(f"❌ Файл сессии не найден: {SESSION_NAME}.session")
        return
    
    print(f"🔍 Использую сессию: {SESSION_NAME}")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()
    
    try:
        me = await client.get_me()
        print(f"✅ Аккаунт: {me.first_name} (ID: {me.id})")
        
        # Пытаемся найти бота
        print(f"🔍 Ищу бота {BOT_USERNAME}...")
        bot = await client.get_entity(BOT_USERNAME)
        
        print(f"\n✅ Бот найден!")
        print(f"   ID: {bot.id}")
        print(f"   Username: {bot.username}")
        
        # Сохраняем ID
        with open('bot_id.txt', 'w') as f:
            f.write(str(bot.id))
        print("\n✅ ID сохранен в bot_id.txt")
        
        # Отправляем /start для проверки
        print("\n📤 Отправляю /start...")
        await client.send_message(bot, '/start')
        print("✅ Отправлен /start")
        
        await asyncio.sleep(2)
        
        # Получаем ответ
        print("\n📩 Получаю ответ...")
        async for msg in client.iter_messages(bot, limit=1):
            if msg.text:
                print(f"Ответ бота: {msg.text[:200]}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
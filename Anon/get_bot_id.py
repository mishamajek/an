import asyncio
import os
import glob
from telethon import TelegramClient

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'
BOT_USERNAME = '@MessageAnonBot'

async def main():
    # Находим все сессии
    session_files = glob.glob("sessions/*.session")
    
    if not session_files:
        print("❌ Нет файлов сессий в папке sessions/")
        return
    
    print("📁 Найдены сессии:")
    for f in session_files:
        print(f"   {f}")
    
    # Используем первую найденную сессию
    session_path = session_files[0].replace('.session', '')
    print(f"\n🔍 Использую сессию: {session_path}")
    
    client = TelegramClient(session_path, API_ID, API_HASH)
    await client.start()
    
    try:
        me = await client.get_me()
        print(f"✅ Аккаунт: {me.first_name} (ID: {me.id})")
        
        bot = await client.get_entity(BOT_USERNAME)
        print(f"\n✅ Бот найден!")
        print(f"   ID: {bot.id}")
        print(f"   Username: {bot.username}")
        print(f"   Access Hash: {bot.access_hash}")
        
        # Сохраняем ID
        with open('bot_id.txt', 'w') as f:
            f.write(str(bot.id))
        print("\n✅ ID сохранен в bot_id.txt")
        
        # Отправляем /start для проверки
        await client.send_message(bot, '/start')
        print("✅ Отправлен /start")
        
        await asyncio.sleep(2)
        
        # Получаем ответ
        async for msg in client.iter_messages(bot, limit=1):
            if msg.text:
                print(f"📩 Ответ бота: {msg.text[:200]}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
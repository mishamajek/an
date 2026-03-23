import asyncio
from telethon import TelegramClient

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'
BOT_USERNAME = '@MessageAnonBot'

async def main():
    # Используем любой рабочий аккаунт (тот, который уже работал)
    client = TelegramClient('sessions/user_17788323682', API_ID, API_HASH)
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
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
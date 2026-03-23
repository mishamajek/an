import asyncio
import os
import glob
from telethon import TelegramClient
from telethon.tl.types import KeyboardButtonCallback

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'
BOT_USERNAME = '@MessageAnonBot'
SESSIONS_FOLDER = 'sessions'

# Настройки регистрации
GENDER = 'Мужской'  # или 'Женский'
AGE = '25'  # от 18 до 99

async def register_account(session_path):
    """Регистрирует аккаунт в боте"""
    try:
        print(f"🔄 Регистрация: {os.path.basename(session_path)}")
        
        client = TelegramClient(session_path, API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"❌ Сессия не авторизована")
            return False
        
        me = await client.get_me()
        print(f"✅ Аккаунт: {me.first_name} (ID: {me.id})")
        
        # Находим бота
        bot = await client.get_entity('@MessageAnonBot')
        print(f"✅ Бот найден")
        
        # Отправляем /start
        await client.send_message(bot, '/start')
        print(f"📤 Отправлен /start")
        
        # Ждем ответ
        await asyncio.sleep(2)
        
        # Получаем последнее сообщение
        async for msg in client.iter_messages(bot, limit=1):
            if msg.text and ('пол' in msg.text.lower() or 'регистрация' in msg.text.lower()):
                print(f"📩 Получен вопрос: {msg.text[:100]}")
                
                # Ищем кнопки
                if msg.reply_markup:
                    print("🔘 Найдены кнопки!")
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            if hasattr(button, 'text'):
                                btn_text = button.text
                                print(f"   Кнопка: {btn_text}")
                                
                                if GENDER in btn_text:
                                    await msg.click(text=btn_text)
                                    print(f"✅ Нажата кнопка: {btn_text}")
                                    await asyncio.sleep(2)
                                    
                                    # Отправляем возраст
                                    await client.send_message(bot, AGE)
                                    print(f"✅ Отправлен возраст: {AGE}")
                                    return True
        return False
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        await client.disconnect()

async def main():
    print("="*60)
    print("🚀 АВТОМАТИЧЕСКАЯ РЕГИСТРАЦИЯ В БОТЕ")
    print("="*60)
    print(f"Пол: {GENDER}")
    print(f"Возраст: {AGE}")
    print("="*60)
    
    session_files = glob.glob(os.path.join(SESSIONS_FOLDER, "*.session"))
    
    success = 0
    for session_file in session_files:
        if await register_account(session_file):
            success += 1
        print()
    
    print(f"✅ Зарегистрировано аккаунтов: {success}/{len(session_files)}")

if __name__ == '__main__':
    asyncio.run(main())
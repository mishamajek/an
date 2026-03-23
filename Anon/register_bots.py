import asyncio
import os
import glob
from telethon import TelegramClient
from telethon.tl.types import KeyboardButtonCallback
from telethon.tl.functions.contacts import ResolveUsernameRequest

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'
SESSIONS_FOLDER = 'sessions'

# Настройки регистрации
GENDER = 'Мужской'  # или 'Женский'
AGE = '25'  # от 18 до 99

async def find_bot_in_dialogs(client):
    """Находит бота через диалоги (самый надежный способ)"""
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_user and dialog.entity and hasattr(dialog.entity, 'username'):
                username = dialog.entity.username or ''
                # Проверяем разные варианты имени
                if 'MessageAnonBot' in username or 'messageanon' in username.lower() or 'Анонимный чат' in str(dialog.name):
                    print(f"✅ Бот найден в диалогах: {dialog.name} (@{username})")
                    return dialog.entity
    except Exception as e:
        print(f"Поиск в диалогах: {e}")
    return None

async def send_message_to_bot(client, bot, text):
    """Отправляет сообщение боту и ждет ответ"""
    try:
        await client.send_message(bot, text)
        print(f"📤 Отправлено: {text}")
        await asyncio.sleep(2)
        
        # Получаем последний ответ
        async for msg in client.iter_messages(bot, limit=1):
            if msg.text and msg.out is False:  # Входящее сообщение
                print(f"📩 Ответ: {msg.text[:200]}")
                return msg
        return None
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return None

async def register_account(session_path):
    """Регистрирует аккаунт в боте"""
    try:
        print(f"\n🔄 Регистрация: {os.path.basename(session_path)}")
        
        client = TelegramClient(session_path, API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"❌ Сессия не авторизована")
            return False
        
        me = await client.get_me()
        print(f"✅ Аккаунт: {me.first_name} (ID: {me.id})")
        
        # Находим бота через диалоги (уже есть диалог!)
        bot = await find_bot_in_dialogs(client)
        
        if not bot:
            print(f"❌ Бот не найден в диалогах")
            return False
        
        print(f"✅ Бот найден, отправляем /start...")
        
        # Отправляем /start и ждем ответ
        msg = await send_message_to_bot(client, bot, '/start')
        
        if not msg:
            print(f"❌ Нет ответа на /start")
            return False
        
        # Проверяем, нужно ли проходить регистрацию
        if 'пол' in msg.text.lower() or 'регистрация' in msg.text.lower():
            print("🔘 Начинаем регистрацию...")
            
            # Ищем кнопки
            if msg.reply_markup:
                for row in msg.reply_markup.rows:
                    for button in row.buttons:
                        if hasattr(button, 'text'):
                            btn_text = button.text
                            if GENDER in btn_text:
                                print(f"🔘 Нажимаем кнопку: {btn_text}")
                                await msg.click(text=btn_text)
                                await asyncio.sleep(2)
                                
                                # Отправляем возраст
                                await send_message_to_bot(client, bot, AGE)
                                print(f"✅ Регистрация завершена!")
                                return True
        
        print(f"✅ Аккаунт уже зарегистрирован")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        await client.disconnect()

async def main():
    print("="*60)
    print("🚀 АВТОМАТИЧЕСКАЯ РЕГИСТРАЦИЯ В БОТЕ")
    print("="*60)
    print(f"📋 Настройки регистрации:")
    print(f"   Пол: {GENDER}")
    print(f"   Возраст: {AGE}")
    print("="*60)
    
    session_files = glob.glob(os.path.join(SESSIONS_FOLDER, "*.session"))
    
    if not session_files:
        print("❌ Нет файлов сессий в папке sessions/")
        return
    
    print(f"📁 Найдено сессий: {len(session_files)}\n")
    
    success = 0
    for session_file in session_files:
        if await register_account(session_file):
            success += 1
        print("-"*50)
    
    print("="*60)
    print(f"✅ Зарегистрировано аккаунтов: {success}/{len(session_files)}")
    print("="*60)

if __name__ == '__main__':
    asyncio.run(main())
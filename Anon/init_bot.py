import asyncio
import os
import glob
from telethon import TelegramClient

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'
BOT_USERNAME = '@MessageAnonBot'
SESSIONS_FOLDER = 'sessions'

async def init_bot_for_session(session_path):
    """Инициализирует диалог с ботом для одной сессии"""
    try:
        print(f"🔄 Обработка: {session_path}")
        
        client = TelegramClient(session_path, API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"❌ Сессия не авторизована: {session_path}")
            return False
        
        me = await client.get_me()
        print(f"✅ Аккаунт: {me.first_name} (ID: {me.id})")
        
        # Находим бота
        try:
            bot = await client.get_entity(BOT_USERNAME)
            print(f"✅ Бот найден: {BOT_USERNAME}")
        except Exception as e:
            print(f"❌ Бот не найден: {e}")
            return False
        
        # Отправляем /start
        try:
            await client.send_message(bot, '/start')
            print(f"✅ Отправлен /start")
            
            # Ждем ответа
            await asyncio.sleep(2)
            
            # Проверяем, что диалог создан
            async for dialog in client.iter_dialogs():
                if dialog.is_user and dialog.entity and hasattr(dialog.entity, 'username'):
                    username = dialog.entity.username or ''
                    if 'MessageAnonBot' in username or 'messageanon' in username.lower():
                        print(f"✅ Диалог с ботом создан!")
                        break
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки /start: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        await client.disconnect()

async def main():
    """Главная функция"""
    print("="*60)
    print("🚀 ИНИЦИАЛИЗАЦИЯ ДИАЛОГА С БОТОМ")
    print("="*60)
    
    # Находим все сессии
    session_files = glob.glob(os.path.join(SESSIONS_FOLDER, "*.session"))
    
    if not session_files:
        print("❌ Нет файлов сессий в папке sessions/")
        return
    
    print(f"📁 Найдено сессий: {len(session_files)}")
    print()
    
    success = 0
    failed = 0
    
    for session_file in session_files:
        print("-"*40)
        if await init_bot_for_session(session_file):
            success += 1
        else:
            failed += 1
        print()
    
    print("="*60)
    print(f"✅ Успешно: {success}")
    print(f"❌ Ошибок: {failed}")
    print("="*60)
    print("\nТеперь можно запускать основного бота!")

if __name__ == '__main__':
    asyncio.run(main())
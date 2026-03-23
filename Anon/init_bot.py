import asyncio
import os
import glob
from telethon import TelegramClient

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'
BOT_USERNAME = '@MessageAnonBot'  # Оставляем как есть, с большой буквы
BOT_USERNAME_SEARCH = ['MessageAnonBot', 'messageanonbot', 'MessageAnon', 'messageanon']
SESSIONS_FOLDER = 'sessions'

async def find_bot(client):
    """Находит бота разными способами"""
    
    # Способ 1: через get_entity с точным именем
    try:
        bot = await client.get_entity('@MessageAnonBot')
        print(f"✅ Бот найден через get_entity: @MessageAnonBot")
        return bot
    except Exception as e:
        print(f"   get_entity(@MessageAnonBot): {e}")
    
    # Способ 2: через get_entity с маленькими буквами
    try:
        bot = await client.get_entity('@messageanonbot')
        print(f"✅ Бот найден через get_entity: @messageanonbot")
        return bot
    except Exception as e:
        print(f"   get_entity(@messageanonbot): {e}")
    
    # Способ 3: через ResolveUsernameRequest
    try:
        from telethon.tl.functions.contacts import ResolveUsernameRequest
        result = await client(ResolveUsernameRequest('MessageAnonBot'))
        bot = result.peer
        print(f"✅ Бот найден через ResolveUsername: MessageAnonBot")
        return bot
    except Exception as e:
        print(f"   ResolveUsername(MessageAnonBot): {e}")
    
    # Способ 4: через ResolveUsernameRequest с маленькими буквами
    try:
        from telethon.tl.functions.contacts import ResolveUsernameRequest
        result = await client(ResolveUsernameRequest('messageanonbot'))
        bot = result.peer
        print(f"✅ Бот найден через ResolveUsername: messageanonbot")
        return bot
    except Exception as e:
        print(f"   ResolveUsername(messageanonbot): {e}")
    
    # Способ 5: поиск в диалогах
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_user and dialog.entity and hasattr(dialog.entity, 'username'):
                username = dialog.entity.username or ''
                if username.lower() in ['messageanonbot', 'messageanon']:
                    print(f"✅ Бот найден в диалогах: @{username}")
                    return dialog.entity
    except Exception as e:
        print(f"   Поиск в диалогах: {e}")
    
    return None

async def init_bot_for_session(session_path):
    """Инициализирует диалог с ботом для одной сессии"""
    try:
        print(f"🔄 Обработка: {os.path.basename(session_path)}")
        
        client = TelegramClient(session_path, API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"❌ Сессия не авторизована")
            return False
        
        me = await client.get_me()
        print(f"✅ Аккаунт: {me.first_name} (ID: {me.id})")
        
        # Находим бота
        bot = await find_bot(client)
        
        if not bot:
            print(f"❌ Бот не найден ни одним способом")
            return False
        
        # Отправляем /start
        try:
            await client.send_message(bot, '/start')
            print(f"✅ Отправлен /start")
            
            # Ждем ответа
            await asyncio.sleep(3)
            
            # Проверяем ответ
            async for message in client.iter_messages(bot, limit=1):
                if message.text:
                    print(f"📩 Ответ бота: {message.text[:100]}")
                    if "регистрация" in message.text.lower() or "пол" in message.text.lower():
                        print(f"⚠️ Бот требует регистрации! Нужно пройти регистрацию вручную.")
            
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
    
    session_files = glob.glob(os.path.join(SESSIONS_FOLDER, "*.session"))
    
    if not session_files:
        print("❌ Нет файлов сессий в папке sessions/")
        return
    
    print(f"📁 Найдено сессий: {len(session_files)}")
    print()
    
    success = 0
    failed = 0
    
    for session_file in session_files:
        print("-"*50)
        if await init_bot_for_session(session_file):
            success += 1
        else:
            failed += 1
        print()
    
    print("="*60)
    print(f"✅ Успешно: {success}")
    print(f"❌ Ошибок: {failed}")
    print("="*60)
    print("\nЕсли бот требует регистрации, нужно пройти её вручную один раз.")

if __name__ == '__main__':
    asyncio.run(main())
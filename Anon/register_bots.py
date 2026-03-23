import asyncio
import os
import glob
from telethon import TelegramClient
from telethon.tl.types import KeyboardButtonCallback
from telethon.tl.functions.contacts import ResolveUsernameRequest

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'
BOT_USERNAME = '@MessageAnonBot'
BOT_USERNAME_WITHOUT_AT = 'MessageAnonBot'
SESSIONS_FOLDER = 'sessions'

# Настройки регистрации
GENDER = 'Мужской'  # или 'Женский'
AGE = '25'  # от 18 до 99

async def find_bot(client):
    """Находит бота несколькими способами"""
    
    # Способ 1: через get_entity
    try:
        bot = await client.get_entity('@MessageAnonBot')
        print(f"✅ Бот найден через get_entity")
        return bot
    except Exception as e:
        pass
    
    # Способ 2: через ResolveUsernameRequest
    try:
        result = await client(ResolveUsernameRequest('MessageAnonBot'))
        bot = result.peer
        print(f"✅ Бот найден через ResolveUsername")
        return bot
    except Exception as e:
        pass
    
    # Способ 3: поиск в диалогах
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_user and dialog.entity and hasattr(dialog.entity, 'username'):
                username = dialog.entity.username or ''
                if 'MessageAnonBot' in username or 'messageanon' in username.lower():
                    print(f"✅ Бот найден в диалогах: @{username}")
                    return dialog.entity
    except Exception as e:
        pass
    
    # Способ 4: через get_input_entity
    try:
        bot = await client.get_input_entity('MessageAnonBot')
        print(f"✅ Бот найден через get_input_entity")
        return bot
    except Exception as e:
        pass
    
    return None

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
        bot = await find_bot(client)
        
        if not bot:
            print(f"❌ Бот не найден")
            return False
        
        print(f"✅ Бот найден")
        
        # Отправляем /start
        await client.send_message(bot, '/start')
        print(f"📤 Отправлен /start")
        
        # Ждем ответ
        await asyncio.sleep(3)
        
        # Получаем последнее сообщение
        async for msg in client.iter_messages(bot, limit=1):
            if msg.text:
                print(f"📩 Ответ бота: {msg.text[:200]}")
                
                # Проверяем, есть ли кнопки
                if msg.reply_markup:
                    print("🔘 Найдены кнопки!")
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            if hasattr(button, 'text'):
                                btn_text = button.text
                                print(f"   Кнопка: {btn_text}")
                                
                                # Ищем кнопку с выбранным полом
                                if GENDER in btn_text:
                                    await msg.click(text=btn_text)
                                    print(f"✅ Нажата кнопка: {btn_text}")
                                    await asyncio.sleep(2)
                                    
                                    # Отправляем возраст
                                    await client.send_message(bot, AGE)
                                    print(f"✅ Отправлен возраст: {AGE}")
                                    await asyncio.sleep(2)
                                    return True
                else:
                    # Если нет кнопок, возможно вопрос о возрасте
                    if 'возраст' in msg.text.lower() or 'лет' in msg.text.lower():
                        await client.send_message(bot, AGE)
                        print(f"✅ Отправлен возраст: {AGE}")
                        await asyncio.sleep(2)
                        return True
        return False
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        await client.disconnect()

async def check_bot_exists():
    """Проверяет, существует ли бот в принципе"""
    try:
        from telethon import TelegramClient
        import asyncio
        
        # Создаем временную сессию
        client = TelegramClient('temp', API_ID, API_HASH)
        await client.connect()
        
        # Проверяем существование бота
        try:
            bot = await client.get_entity('@MessageAnonBot')
            print(f"✅ Бот @MessageAnonBot существует! ID: {bot.id}")
            return True
        except Exception as e:
            print(f"❌ Бот @MessageAnonBot НЕ существует: {e}")
            return False
        finally:
            await client.disconnect()
    except Exception as e:
        print(f"Ошибка проверки: {e}")
        return False

async def main():
    print("="*60)
    print("🚀 АВТОМАТИЧЕСКАЯ РЕГИСТРАЦИЯ В БОТЕ")
    print("="*60)
    
    # Сначала проверяем, существует ли бот
    print("\n🔍 Проверка существования бота...")
    bot_exists = await check_bot_exists()
    
    if not bot_exists:
        print("\n❌ Бот @MessageAnonBot не существует!")
        print("Проверьте правильность username бота.")
        return
    
    print(f"\n📋 Настройки регистрации:")
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
        print("-"*50)
        if await register_account(session_file):
            success += 1
        print()
    
    print("="*60)
    print(f"✅ Зарегистрировано аккаунтов: {success}/{len(session_files)}")
    print("="*60)

if __name__ == '__main__':
    asyncio.run(main())
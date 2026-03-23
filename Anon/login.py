import asyncio
import os
import glob
from telethon import TelegramClient, events

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'

async def monitor_account(session_path, session_name):
    """Мониторит сообщения для одного аккаунта"""
    client = TelegramClient(session_path, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"⚠️ {session_name}: не авторизован")
            return
        
        me = await client.get_me()
        print(f"✅ {session_name}: {me.first_name} ({me.phone}) - мониторинг запущен")
        
        # Обработчик всех входящих сообщений
        @client.on(events.NewMessage)
        async def handler(event):
            message_text = event.message.text or "[Нет текста]"
            sender = await event.get_sender()
            sender_name = sender.first_name if sender else "Неизвестно"
            
            print(f"\n{'─'*60}")
            print(f"📱 {session_name} ({me.phone})")
            print(f"👤 От: {sender_name}")
            print(f"🕐 {event.message.date.strftime('%H:%M:%S')}")
            print(f"📝 {message_text}")
            if event.message.media:
                print(f"📎 Медиа: {type(event.message.media).__name__}")
            print(f"{'─'*60}")
        
        # Держим соединение открытым
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ {session_name}: ошибка - {e}")

async def main():
    print("\n" + "="*60)
    print("📡 МОНИТОРИНГ СООБЩЕНИЙ АККАУНТОВ")
    print("="*60)
    print("\nСкрипт показывает ВСЕ сообщения, которые приходят на аккаунты")
    print("Вы сами запрашиваете код на телефоне")
    print("Когда код придет, вы увидите его в консоли")
    print("="*60)
    
    # Находим все сессии
    session_files = glob.glob("sessions/*.session")
    
    if not session_files:
        print("\n❌ Нет файлов сессий в папке sessions/")
        return
    
    print(f"\n📁 Найдено сессий: {len(session_files)}\n")
    
    # Запускаем мониторинг для всех авторизованных сессий
    tasks = []
    for session_file in session_files:
        session_path = session_file.replace('.session', '')
        session_name = os.path.basename(session_file).replace('.session', '')
        
        client = TelegramClient(session_path, API_ID, API_HASH)
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ {session_name}: {me.first_name} ({me.phone})")
            await client.disconnect()
            
            # Запускаем мониторинг
            task = asyncio.create_task(monitor_account(session_path, session_name))
            tasks.append(task)
        else:
            print(f"⚠️ {session_name}: не авторизован")
            await client.disconnect()
    
    if not tasks:
        print("\n❌ Нет авторизованных сессий для мониторинга")
        return
    
    print(f"\n🚀 Запущено {len(tasks)} мониторов")
    print("📡 Ожидание сообщений...\n")
    
    # Ждем завершения всех задач (бесконечно)
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Мониторинг остановлен")
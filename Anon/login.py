import asyncio
import os
import glob
from telethon import TelegramClient, events

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'

async def monitor_session(session_path, session_name, phone):
    """Мониторит сообщения для указанного аккаунта"""
    print(f"\n{'='*60}")
    print(f"📱 АККАУНТ: {session_name}")
    print(f"📞 Номер: {phone}")
    print(f"{'='*60}")
    
    client = TelegramClient(session_path, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        # Проверяем, авторизован ли аккаунт
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ Аккаунт уже авторизован!")
            print(f"   Имя: {me.first_name}")
            print(f"   Телефон: {me.phone}")
            print(f"   ID: {me.id}")
            
            # Спрашиваем, нужно ли выйти
            logout = input("\n🔓 Выйти из аккаунта? (y/n): ").strip().lower()
            if logout == 'y':
                await client.log_out()
                print("✅ Выполнен выход, теперь можно войти заново")
            else:
                await client.disconnect()
                return
        
        # Обработчик всех входящих сообщений
        @client.on(events.NewMessage)
        async def handler(event):
            message_text = event.message.text or "[Нет текста]"
            sender = await event.get_sender()
            sender_name = sender.first_name if sender else "Неизвестно"
            
            print(f"\n{'─'*50}")
            print(f"📩 НОВОЕ СООБЩЕНИЕ")
            print(f"👤 Отправитель: {sender_name}")
            print(f"🕐 Время: {event.message.date.strftime('%H:%M:%S')}")
            print(f"📝 Текст: {message_text}")
            
            # Если есть медиа
            if event.message.media:
                print(f"📎 Медиа: {type(event.message.media).__name__}")
            
            print(f"{'─'*50}")
        
        print("\n🔍 НАЧАЛО МОНИТОРИНГА")
        print("   Бот показывает ВСЕ сообщения, которые приходят на этот аккаунт")
        print("   Среди них вы увидите код для входа")
        print("   Для остановки нажмите Ctrl+C\n")
        
        # Бесконечный цикл для поддержания работы
        print("⏳ Ожидание сообщений...\n")
        
        try:
            # Ждем, пока пользователь не нажмет Ctrl+C
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Мониторинг остановлен")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

async def main():
    print("\n" + "="*60)
    print("🔍 МОНИТОРИНГ СООБЩЕНИЙ АККАУНТОВ")
    print("="*60)
    print("\nСкрипт показывает ВСЕ сообщения, которые приходят на аккаунт")
    print("Вы сами запрашиваете код на телефоне")
    print("Когда код придет, вы увидите его в консоли")
    print("="*60)
    
    # Находим все сессии
    session_files = glob.glob("sessions/*.session")
    
    if not session_files:
        print("\n❌ Нет файлов сессий в папке sessions/")
        return
    
    print(f"\n📁 Найдено сессий: {len(session_files)}")
    
    # Показываем список сессий
    sessions_list = []
    for i, session_file in enumerate(session_files, 1):
        session_name = os.path.basename(session_file).replace('.session', '')
        print(f"   {i}. {session_name}")
        
        # Проверяем статус
        client = TelegramClient(session_file.replace('.session', ''), API_ID, API_HASH)
        await client.connect()
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"      ✅ Авторизован: {me.first_name} ({me.phone})")
        else:
            print(f"      ❌ Не авторизован")
        await client.disconnect()
        sessions_list.append(session_file)
    
    # Выбор сессии
    print("\n" + "="*60)
    choice = input("🔍 Выберите номер сессии для мониторинга (или 'all' для всех): ").strip()
    
    if choice.lower() == 'all':
        # Сначала собираем номера для всех сессий
        print("\n" + "="*60)
        print("📞 ВВЕДИТЕ НОМЕРА ТЕЛЕФОНОВ")
        print("="*60)
        
        accounts = []
        for session_file in sessions_list:
            session_name = os.path.basename(session_file).replace('.session', '')
            phone = input(f"\nНомер для {session_name} (формат +71234567890): ").strip()
            if not phone.startswith('+'):
                phone = '+' + phone
            accounts.append({
                'session_path': session_file.replace('.session', ''),
                'session_name': session_name,
                'phone': phone
            })
        
        print("\n" + "="*60)
        print("🚀 НАЧАЛО МОНИТОРИНГА ВСЕХ АККАУНТОВ")
        print("="*60)
        print("\nДля каждого аккаунта будет запущен мониторинг")
        print("Сообщения от всех аккаунтов будут выводиться в консоль")
        print("Для остановки нажмите Ctrl+C\n")
        
        input("📌 Нажмите Enter для начала...")
        
        # Запускаем мониторинг для всех аккаунтов
        tasks = []
        for account in accounts:
            task = asyncio.create_task(monitor_session(
                account['session_path'],
                account['session_name'],
                account['phone']
            ))
            tasks.append(task)
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\n\n🛑 Мониторинг всех аккаунтов остановлен")
            for task in tasks:
                task.cancel()
    
    else:
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(sessions_list):
                print("❌ Неверный выбор")
                return
            session_file = sessions_list[idx]
            session_name = os.path.basename(session_file).replace('.session', '')
            
            # Запрашиваем номер телефона
            phone = input(f"\n📞 Введите номер телефона для {session_name} (формат +71234567890): ").strip()
            if not phone.startswith('+'):
                phone = '+' + phone
            
            await monitor_session(session_file.replace('.session', ''), session_name, phone)
            
        except ValueError:
            print("❌ Неверный ввод")
            return

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа остановлена")
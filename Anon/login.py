import asyncio
import os
import glob
import re
from telethon import TelegramClient, events

API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'

async def wait_for_code(session_path, session_name, phone):
    """Ждет код для указанного аккаунта"""
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
            await client.disconnect()
            return
        
        # Создаем событие для ожидания кода
        code_received = asyncio.Event()
        received_code = None
        
        # Обработчик входящих сообщений
        @client.on(events.NewMessage)
        async def handler(event):
            nonlocal received_code
            message_text = event.message.text or ""
            
            # Ищем код (5-6 цифр)
            code_match = re.search(r'\b(\d{5,6})\b', message_text)
            if code_match:
                received_code = code_match.group(1)
                print(f"\n🔐 ПОЛУЧЕН КОД: {received_code}")
                print(f"📝 Сообщение: {message_text[:200]}")
                code_received.set()
        
        print("\n⏳ Ожидаю код...")
        print("   Когда вы запросите код на телефоне, он придет сюда")
        print("   Скрипт автоматически перехватит и покажет его")
        print("   Для перехода к следующему аккаунту нажмите Enter\n")
        
        # Ждем код
        try:
            await asyncio.wait_for(code_received.wait(), timeout=300)
            
            if received_code:
                print(f"\n{'─'*40}")
                print(f"✅ КОД ДЛЯ ВХОДА: {received_code}")
                print(f"📱 Аккаунт: {phone}")
                print(f"{'─'*40}")
            
            input("\n📌 Нажмите Enter для перехода к следующему аккаунту...")
            
        except asyncio.TimeoutError:
            print("\n⏰ Таймаут: код не получен в течение 5 минут")
            input("📌 Нажмите Enter для продолжения...")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

async def main():
    print("\n" + "="*60)
    print("🔐 ПЕРЕХВАТ КОДОВ ДЛЯ ВХОДА В АККАУНТЫ")
    print("="*60)
    print("\nВы сами запрашиваете код на телефоне.")
    print("Скрипт просто ждет, пока код придет в Telegram,")
    print("перехватывает его и показывает вам.")
    print("="*60)
    
    # Находим все сессии
    session_files = glob.glob("sessions/*.session")
    
    if not session_files:
        print("\n❌ Нет файлов сессий в папке sessions/")
        return
    
    print(f"\n📁 Найдено сессий: {len(session_files)}")
    
    # Сначала выводим список сессий
    sessions_info = []
    for i, session_file in enumerate(session_files, 1):
        session_name = os.path.basename(session_file).replace('.session', '')
        print(f"   {i}. {session_name}")
        
        # Проверяем авторизацию
        client = TelegramClient(session_file.replace('.session', ''), API_ID, API_HASH)
        await client.connect()
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"      ✅ Авторизован: {me.first_name} ({me.phone})")
        else:
            print(f"      ❌ Не авторизован")
        await client.disconnect()
    
    # Собираем номера телефонов
    print("\n" + "="*60)
    print("📞 ВВЕДИТЕ НОМЕРА ТЕЛЕФОНОВ")
    print("="*60)
    
    accounts = []
    for session_file in session_files:
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
    print("🚀 НАЧАЛО ПЕРЕХВАТА КОДОВ")
    print("="*60)
    print("\nТеперь запрашивайте код на телефоне для каждого аккаунта.")
    print("Как только код придет, он появится здесь.")
    print("="*60)
    
    input("\n📌 Нажмите Enter для начала...")
    
    # Обрабатываем каждый аккаунт
    for i, account in enumerate(accounts, 1):
        print(f"\n{'─'*60}")
        print(f"📌 АККАУНТ {i} ИЗ {len(accounts)}")
        await wait_for_code(
            account['session_path'],
            account['session_name'],
            account['phone']
        )
    
    print("\n" + "="*60)
    print("✅ ОБРАБОТКА ЗАВЕРШЕНА")
    print("="*60)

if __name__ == '__main__':
    asyncio.run(main())
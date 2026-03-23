import asyncio
import logging
import re
import time
import os
import sys
import io
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import signal
from typing import List, Dict, Optional
import glob

from telethon import TelegramClient, events, functions
from telethon.errors import FloodWaitError, SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError, PeerIdInvalidError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, KeyboardButtonCallback
from telethon.tl.custom import Message
from telethon.tl.functions.messages import StartBotRequest

# Фикс для отображения эмодзи в Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройки (API данные нужно получить на my.telegram.org)
API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'

# ID бота
BOT_USERNAME = '@MessageAnonBot'

# Папки и файлы
SESSIONS_FOLDER = 'sessions'
MESSAGE_FILE = 'message.txt'
LOG_FOLDER = 'logs'
STATS_FILE = 'stats.json'

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('mass_sender.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Создаем необходимые папки
os.makedirs(SESSIONS_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)


# ================== ПОЛНЫЙ СЛОВАРЬ ЭМОДЗИ ==================
# (сохраните ваш существующий словарь EMOJI_DICT здесь)
EMOJI_DICT = {
    'кот': ['🐱', '😺', '😸', '😻', '😽', '🙀', '😿', '😾', '🐈', '🐆'],
    'собака': ['🐶', '🐕', '🦮', '🐕‍🦺', '🐩'],
    'мышь': ['🐭', '🐁', '🐀'],
    'змея': ['🐍'],
    'птица': ['🐦', '🦅'],
    'рыба': ['🐟', '🐠'],
}


class SessionCreator:
    """Класс для создания новых сессий"""
    
    @staticmethod
    async def create_new_session():
        """Создает новую сессию через ввод номера и кода"""
        print("\n" + "="*50)
        print("📱 СОЗДАНИЕ НОВОЙ СЕССИИ")
        print("="*50)
        
        phone = input("📞 Введите номер телефона в формате +71234567890: ").strip()
        if not phone.startswith('+'):
            phone = '+' + phone
        
        session_name = f"user_{phone.replace('+', '')}"
        session_path = os.path.join(SESSIONS_FOLDER, session_name)
        
        print(f"🔄 Подключение к Telegram...")
        
        try:
            client = TelegramClient(session_path, API_ID, API_HASH)
            await client.connect()
            
            if await client.is_user_authorized():
                print("✅ Аккаунт уже авторизован!")
                await client.disconnect()
                return session_name
            
            await client.send_code_request(phone)
            print("📱 Код подтверждения отправлен!")
            
            code = input("🔢 Введите код из Telegram: ").strip().replace(' ', '').replace('-', '')
            
            try:
                await client.sign_in(phone, code)
                print("✅ Аккаунт успешно добавлен!")
                await client.disconnect()
                return session_name
                
            except SessionPasswordNeededError:
                password = input("🔐 Введите пароль 2FA: ").strip()
                await client.sign_in(password=password)
                print("✅ Аккаунт успешно добавлен (с 2FA)!")
                await client.disconnect()
                return session_name
                
            except PhoneCodeInvalidError:
                print("❌ Неверный код!")
                await client.disconnect()
                return None
                
        except FloodWaitError as e:
            print(f"❌ Слишком много попыток. Подождите {e.seconds} секунд")
            return None
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None
    
    @staticmethod
    async def add_multiple_accounts(max_accounts=10):
        """Добавляет несколько аккаунтов"""
        existing_sessions = glob.glob(os.path.join(SESSIONS_FOLDER, "*.session"))
        current_count = len(existing_sessions)
        
        print(f"\n📊 Текущее количество сессий: {current_count}")
        print(f"📊 Максимум можно добавить: {max_accounts}")
        
        if current_count >= max_accounts:
            print(f"✅ Уже достигнут лимит в {max_accounts} аккаунтов")
            return
        
        remaining = max_accounts - current_count
        print(f"✨ Можно добавить еще: {remaining} аккаунтов")
        
        while current_count < max_accounts:
            print(f"\n--- Добавление аккаунта {current_count + 1} из {max_accounts} ---")
            result = await SessionCreator.create_new_session()
            
            if result:
                current_count += 1
                print(f"✅ Аккаунт добавлен! Всего: {current_count}/{max_accounts}")
                
                if current_count < max_accounts:
                    answer = input("\n➕ Добавить еще один аккаунт? (y/n): ").strip().lower()
                    if answer != 'y':
                        break
            else:
                print("❌ Не удалось добавить аккаунт")
                retry = input("🔄 Попробовать снова? (y/n): ").strip().lower()
                if retry != 'y':
                    break


class MultiAccountSender:
    """Класс для управления несколькими аккаунтами"""
    
    def __init__(self):
        self.accounts: List['AccountSender'] = []
        self.message_text = self.load_message()
        self.running = True
        self.global_stats = self.load_stats()
        self.startup_complete = asyncio.Event()
        
    def load_message(self) -> str:
        try:
            if os.path.exists(MESSAGE_FILE):
                with open(MESSAGE_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        logger.info(f"✅ Загружено сообщение из {MESSAGE_FILE}")
                        return content
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки сообщения: {e}")
        
        default_msg = """Привет! Это тестовое сообщение.

Оно может содержать несколько абзацев.
И даже эмодзи! 🎉✨

С уважением,
Отправитель"""
        
        try:
            with open(MESSAGE_FILE, 'w', encoding='utf-8') as f:
                f.write(default_msg)
            logger.info(f"✅ Создан файл {MESSAGE_FILE} с сообщением по умолчанию")
        except:
            pass
        
        return default_msg
    
    def load_stats(self) -> dict:
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'total_sent': 0, 'total_errors': 0, 'captcha_solved': 0, 'captcha_failed': 0}
    
    def save_stats(self):
        try:
            with open(STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.global_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения статистики: {e}")
    
    def find_session_files(self) -> List[str]:
        session_files = []
        for file in glob.glob(os.path.join(SESSIONS_FOLDER, "*.session")):
            session_name = os.path.splitext(os.path.basename(file))[0]
            session_files.append(session_name)
        return session_files
    
    async def initialize_accounts(self):
        session_names = self.find_session_files()
        
        if not session_names:
            print("\n⚠️ Нет файлов сессий!")
            print("="*50)
            print("📱 НУЖНО ДОБАВИТЬ АККАУНТЫ")
            print("="*50)
            
            await SessionCreator.add_multiple_accounts(10)
            
            session_names = self.find_session_files()
            if not session_names:
                print("\n❌ Не добавлено ни одного аккаунта. Выход...")
                return False
        
        logger.info(f"📁 Найдено {len(session_names)} файлов сессий")
        
        for session_name in session_names:
            logger.info(f"🔄 Инициализация аккаунта: {session_name}")
            
            account_log = os.path.join(LOG_FOLDER, f"{session_name}.log")
            
            client = TelegramClient(
                os.path.join(SESSIONS_FOLDER, session_name),
                API_ID,
                API_HASH
            )
            
            account = AccountSender(
                session_name=session_name,
                client=client,
                message_text=self.message_text,
                global_stats=self.global_stats,
                log_file=account_log
            )
            
            if await account.initialize():
                self.accounts.append(account)
                logger.info(f"✅ Аккаунт {session_name} готов к работе")
            else:
                logger.error(f"❌ Не удалось инициализировать аккаунт {session_name}")
        
        logger.info(f"✅ Готово аккаунтов: {len(self.accounts)} из {len(session_names)}")
        
        self.startup_complete.set()
        return len(self.accounts) > 0
    
    async def start_all(self):
        logger.info(f"🚀 Запуск рассылки на {len(self.accounts)} аккаунтах")
        tasks = [account.run() for account in self.accounts]
        await asyncio.gather(*tasks)
    
    async def stop_all(self):
        logger.info("⏸️ Остановка всех аккаунтов...")
        for account in self.accounts:
            account.stop()
    
    async def auto_start(self):
        """Автоматический запуск рассылки после инициализации"""
        await self.startup_complete.wait()
        
        await asyncio.sleep(3)
        
        if not self.accounts:
            logger.error("❌ Нет активных аккаунтов для автоматического запуска")
            return
        
        logger.info("="*70)
        logger.info("🤖 АВТОМАТИЧЕСКИЙ ЗАПУСК РАССЫЛКИ")
        logger.info(f"📊 Аккаунтов: {len(self.accounts)}")
        logger.info(f"📄 Сообщение: {self.message_text[:100]}..." if len(self.message_text) > 100 else f"📄 Сообщение: {self.message_text}")
        logger.info("="*70)
        
        await self.start_all()


class AccountSender:
    """Класс для отдельного аккаунта"""
    
    def __init__(self, session_name: str, client: TelegramClient, message_text: str, 
                 global_stats: dict, log_file: str):
        self.session_name = session_name
        self.client = client
        self.message_text = message_text
        self.global_stats = global_stats
        
        # Настройка логирования для аккаунта
        self.logger = logging.getLogger(f"Account_{session_name}")
        self.logger.setLevel(logging.INFO)
        
        # Добавляем файловый обработчик
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        # Состояние аккаунта
        self.bot_entity = None
        self.waiting_for_next = False
        self.sending_enabled = False
        self.send_count = 0
        self.error_count = 0
        self.running = True
        self.registered = False
        self.registration_step = 0
        
        # Защита от множественных вызовов
        self.last_next_command_time = 0
        self.next_command_cooldown = 5
        self.processing_captcha = False
        self.too_many_requests_cooldown = 300
        
        # Статистика капчи
        self.captcha_stats = {
            'solved': 0,
            'failed': 0,
            'unknown': defaultdict(int)
        }
        
        # Отладка
        self.debug_mode = True
        self.save_photos = False
        self.photos_folder = os.path.join('received_photos', session_name)
        
        # Последний обработанный message_id
        self.last_processed_message_id = None
        
    async def initialize(self) -> bool:
        """Инициализация аккаунта"""
        try:
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                self.logger.warning(f"⚠️ Аккаунт {self.session_name} не авторизован")
                return False
            
            me = await self.client.get_me()
            if me:
                self.logger.info(f"✅ Авторизован как: {me.first_name} (ID: {me.id})")
            
            # Находим бота
            try:
                self.bot_entity = await self.client.get_input_entity(BOT_USERNAME)
                self.logger.info(f"✅ Бот {BOT_USERNAME} найден")
            except Exception as e:
                self.logger.error(f"❌ Не удалось найти бота: {e}")
                return False
            
            # Регистрируем обработчик сообщений
            @self.client.on(events.NewMessage(chats=[self.bot_entity]))
            async def handler(event):
                await self.handle_bot_message(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def ensure_bot_entity(self):
        """Обновляет сущность бота, если нужно"""
        try:
            self.bot_entity = await self.client.get_input_entity(BOT_USERNAME)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка обновления сущности бота: {e}")
            return False
    
    async def run(self):
        """Запускает рассылку на аккаунте"""
        if not self.sending_enabled:
            self.sending_enabled = True
            self.waiting_for_next = False
            self.last_next_command_time = 0
            self.registered = False
            self.registration_step = 0
            self.logger.info("🚀 Рассылка запущена")
            await self.send_next_command()
    
    def stop(self):
        """Останавливает рассылку на аккаунте"""
        self.sending_enabled = False
        self.waiting_for_next = False
        self.logger.info("⏸️ Рассылка остановлена")
    
    async def send_next_command(self):
        """Отправка команды /next"""
        if not self.sending_enabled:
            return
        
        # Обновляем сущность бота перед отправкой
        await self.ensure_bot_entity()
        
        current_time = time.time()
        time_since_last = current_time - self.last_next_command_time
        
        if time_since_last < self.next_command_cooldown:
            await asyncio.sleep(self.next_command_cooldown - time_since_last)
        
        try:
            await self.client.send_message(self.bot_entity, '/next')
            self.waiting_for_next = True
            self.last_next_command_time = time.time()
            self.send_count += 1
            self.global_stats['total_sent'] = self.global_stats.get('total_sent', 0) + 1
            self.logger.info(f"📤 [{self.send_count}] Отправлена команда /next")
            
        except FloodWaitError as e:
            wait_time = e.seconds
            self.logger.warning(f"⚠️ Flood wait: {wait_time}с")
            self.error_count += 1
            self.global_stats['total_errors'] = self.global_stats.get('total_errors', 0) + 1
            await asyncio.sleep(wait_time)
            await self.send_next_command()
            
        except PeerIdInvalidError:
            self.logger.warning("⚠️ Ошибка PeerIdInvalid, обновляем сущность бота...")
            await self.ensure_bot_entity()
            await asyncio.sleep(1)
            await self.send_next_command()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка /next: {e}")
            self.error_count += 1
            self.global_stats['total_errors'] = self.global_stats.get('total_errors', 0) + 1
            await asyncio.sleep(5)
            await self.send_next_command()
    
    async def handle_registration(self, event):
        """Обрабатывает регистрационные сообщения (выбор пола, возраст)"""
        message_text = event.raw_text
        message = event.message
        
        print(f"\n📝 [{self.session_name}] РЕГИСТРАЦИЯ:")
        print(f"Текст: {message_text}")
        
        # Шаг 1: Выбор пола
        if self.registration_step == 0:
            if message.reply_markup:
                buttons = []
                if hasattr(message.reply_markup, 'rows'):
                    for row in message.reply_markup.rows:
                        for button in row.buttons:
                            if hasattr(button, 'text'):
                                buttons.append(button)
                elif hasattr(message.reply_markup, 'buttons'):
                    for row in message.reply_markup.buttons:
                        for button in row:
                            if hasattr(button, 'text'):
                                buttons.append(button)
                
                for button in buttons:
                    btn_text = button.text.lower()
                    if 'мужской' in btn_text or 'муж' in btn_text:
                        print(f"🔘 [{self.session_name}] Нажимаю кнопку: {button.text}")
                        await event.click(text=button.text)
                        self.registration_step = 1
                        self.waiting_for_next = False
                        print(f"✅ [{self.session_name}] Выбран пол, ожидаю вопрос о возрасте...")
                        return
                    elif 'женский' in btn_text or 'жен' in btn_text:
                        print(f"🔘 [{self.session_name}] Нажимаю кнопку: {button.text}")
                        await event.click(text=button.text)
                        self.registration_step = 1
                        self.waiting_for_next = False
                        print(f"✅ [{self.session_name}] Выбран пол, ожидаю вопрос о возрасте...")
                        return
        
        # Шаг 2: Ввод возраста
        elif self.registration_step == 1:
            import re
            numbers = re.findall(r'\b(1[8-9]|[2-9][0-9])\b', message_text)
            if numbers:
                age = numbers[0]
                print(f"🔢 [{self.session_name}] Отправляю возраст: {age}")
                await self.client.send_message(self.bot_entity, age)
                self.registration_step = 2
                self.waiting_for_next = False
                print(f"✅ [{self.session_name}] Возраст отправлен, регистрация завершена!")
                self.registered = True
                await asyncio.sleep(2)
                await self.send_next_command()
                return
        
        await asyncio.sleep(2)
        await self.send_next_command()
    
    def extract_target_name(self, text):
        """Извлекает название из текста капчи"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        match = re.search(r'изображн\(а\)\s+([а-яё]+)', text_lower)
        if match:
            found = match.group(1)
            found = re.sub(r'[.,!?:;()]', '', found)
            return found
        
        match = re.search(r'изображен\(а\)\s+([а-яё]+)', text_lower)
        if match:
            found = match.group(1)
            found = re.sub(r'[.,!?:;()]', '', found)
            return found
        
        match = re.search(r'где\s+([а-яё]+)', text_lower)
        if match:
            found = match.group(1)
            found = re.sub(r'[.,!?:;()]', '', found)
            return found
        
        if 'нажми на кнопку' in text_lower:
            parts = text_lower.split('нажми на кнопку')
            if len(parts) > 1:
                after = parts[1]
                words = after.split()
                for word in words:
                    word = re.sub(r'[.,!?:;()]', '', word)
                    if word in EMOJI_DICT:
                        return word
        
        return None
    
    def find_emoji_button(self, rows, target_name):
        """Ищет кнопку по названию"""
        if not target_name:
            return None
        
        possible_emojis = EMOJI_DICT.get(target_name, [])
        
        if not possible_emojis:
            for key in EMOJI_DICT:
                if target_name in key or key in target_name:
                    possible_emojis = EMOJI_DICT[key]
                    break
        
        if not possible_emojis:
            self.captcha_stats['unknown'][target_name] += 1
            return None
        
        for row in rows:
            if not hasattr(row, 'buttons'):
                continue
                
            for btn in row.buttons:
                if hasattr(btn, 'text'):
                    btn_text = btn.text
                    for emoji in possible_emojis:
                        if emoji in btn_text:
                            return btn
        
        return None
    
    async def handle_captcha(self, event):
        """Обрабатывает капчу"""
        if self.processing_captcha:
            return False
        
        self.processing_captcha = True
        
        try:
            message_text = event.raw_text
            print(f"\n🔐 [{self.session_name}] ПОЛУЧЕНА КАПЧА:")
            print(f"📝 Текст: {message_text[:300]}")
            
            target_name = self.extract_target_name(message_text)
            
            if not target_name:
                self.logger.error("❌ Не удалось определить, что нужно найти в капче")
                self.captcha_stats['failed'] += 1
                self.global_stats['captcha_failed'] = self.global_stats.get('captcha_failed', 0) + 1
                return False
            
            self.logger.info(f"🔍 В капче нужно найти: {target_name}")
            print(f"🔍 [{self.session_name}] В капче нужно найти: {target_name}")
            
            if not event.message.reply_markup or not hasattr(event.message.reply_markup, 'rows'):
                self.logger.error("❌ В сообщении с капчей нет кнопок")
                self.captcha_stats['failed'] += 1
                self.global_stats['captcha_failed'] = self.global_stats.get('captcha_failed', 0) + 1
                return False
            
            target_button = self.find_emoji_button(event.message.reply_markup.rows, target_name)
            
            if not target_button:
                self.logger.error(f"❌ Не удалось найти кнопку с эмодзи для: {target_name}")
                self.captcha_stats['failed'] += 1
                self.global_stats['captcha_failed'] = self.global_stats.get('captcha_failed', 0) + 1
                return False
            
            print(f"✅ [{self.session_name}] Найдена кнопка: {target_button.text}")
            
            captcha_solved = False
            
            try:
                await event.click(text=target_button.text)
                captcha_solved = True
            except:
                pass
            
            if not captcha_solved and hasattr(target_button, 'data'):
                try:
                    await event.click(data=target_button.data)
                    captcha_solved = True
                except:
                    pass
            
            if captcha_solved:
                self.captcha_stats['solved'] += 1
                self.global_stats['captcha_solved'] = self.global_stats.get('captcha_solved', 0) + 1
                self.logger.info(f"✅ Капча решена")
                print(f"✅ [{self.session_name}] Капча решена!")
                
                if self.sending_enabled:
                    await asyncio.sleep(2)
                    await self.send_next_command()
                
                return True
            else:
                self.logger.error("❌ Не удалось решить капчу")
                print(f"❌ [{self.session_name}] Не удалось решить капчу")
                self.captcha_stats['failed'] += 1
                self.global_stats['captcha_failed'] = self.global_stats.get('captcha_failed', 0) + 1
                return False
                
        finally:
            self.processing_captcha = False
    
    def check_for_image(self, event):
        """Проверяет, содержит ли сообщение изображение"""
        if not event.media:
            return False
            
        if isinstance(event.media, MessageMediaPhoto):
            return True
            
        if isinstance(event.media, MessageMediaDocument):
            if event.media.document and event.media.document.mime_type:
                if event.media.document.mime_type.startswith('image/'):
                    return True
        
        return False
    
    async def handle_bot_message(self, event):
        """Обработка сообщений от бота"""
        if not self.sending_enabled:
            return
        
        message_id = event.message.id
        if self.last_processed_message_id == message_id:
            return
        self.last_processed_message_id = message_id
        
        message_text = event.raw_text
        message_media = event.media
        
        print(f"\n📩 [{self.session_name}] Получено сообщение:")
        if message_text:
            print(f"📝 Текст: {message_text[:200]}")
        else:
            print(f"📝 Текст: (пусто)")
        
        if message_media:
            if isinstance(message_media, MessageMediaPhoto):
                print(f"🖼️ Медиа: Фото")
            elif isinstance(message_media, MessageMediaDocument):
                print(f"📄 Медиа: Документ")
            else:
                print(f"📎 Медиа: {type(message_media).__name__}")
        else:
            print(f"📎 Медиа: нет")
        
        # Если аккаунт еще не зарегистрирован, обрабатываем регистрацию
        if not self.registered:
            has_buttons = False
            button_texts = []
            
            if event.message.reply_markup:
                if hasattr(event.message.reply_markup, 'rows'):
                    for row in event.message.reply_markup.rows:
                        for button in row.buttons:
                            if hasattr(button, 'text'):
                                button_texts.append(button.text.lower())
                                has_buttons = True
                elif hasattr(event.message.reply_markup, 'buttons'):
                    for row in event.message.reply_markup.buttons:
                        for button in row:
                            if hasattr(button, 'text'):
                                button_texts.append(button.text.lower())
                                has_buttons = True
            
            if has_buttons and any('муж' in text or 'жен' in text for text in button_texts):
                print(f"🔘 [{self.session_name}] Обнаружена регистрация (выбор пола)")
                await self.handle_registration(event)
                return
            
            if message_text and ('возраст' in message_text.lower() or 'лет' in message_text.lower() or 'от 18 до 99' in message_text.lower()):
                print(f"🔢 [{self.session_name}] Обнаружен вопрос о возрасте")
                await self.handle_registration(event)
                return
        
        # Проверка на ошибку "слишком много запросов"
        if message_text and ("слишком много запросов" in message_text.lower() or 
                             "too many requests" in message_text.lower()):
            self.logger.warning("⚠️ Обнаружена ошибка 'Слишком много запросов'!")
            print(f"⚠️ [{self.session_name}] СЛИШКОМ МНОГО ЗАПРОСОВ! Ожидание {self.too_many_requests_cooldown // 60} минут...")
            
            await asyncio.sleep(self.too_many_requests_cooldown)
            
            if self.sending_enabled:
                await self.send_next_command()
            
            return
        
        # Обработка капчи
        if message_text and ("проверку на робота" in message_text or 
                             "капча" in message_text.lower() or
                             "нажми на кнопку" in message_text):
            
            if event.message.reply_markup and hasattr(event.message.reply_markup, 'rows'):
                self.logger.warning("⚠️ Обнаружена капча!")
                await self.handle_captcha(event)
                return
        
        if self.waiting_for_next:
            if self.check_for_image(event):
                self.waiting_for_next = False
                self.logger.info("✅ Получено подтверждение (изображение)!")
                print(f"✅ [{self.session_name}] Получено подтверждение (изображение)!")
                
                await asyncio.sleep(1.5)
                await self.send_target_message()
            else:
                if message_text and "капча" not in message_text.lower():
                    print(f"ℹ️ [{self.session_name}] Получено текстовое сообщение вместо изображения:")
                    print(f"   {message_text[:200]}")
                    if "не удалось" in message_text.lower() or "ошибка" in message_text.lower():
                        print(f"⚠️ [{self.session_name}] Ошибка от бота, продолжаем цикл")
                        await asyncio.sleep(3)
                        await self.send_next_command()


    async def send_target_message(self):
        """Отправка целевого сообщения"""
        # Обновляем сущность бота перед отправкой
        await self.ensure_bot_entity()
        
        try:
            await self.client.send_message(self.bot_entity, self.message_text)
            self.logger.info(f"✅ Сообщение #{self.send_count} отправлено!")
            print(f"📤 [{self.session_name}] Сообщение #{self.send_count} отправлено!")
            
            await asyncio.sleep(3)
            await self.send_next_command()
            
        except FloodWaitError as e:
            wait_time = e.seconds
            self.logger.warning(f"⚠️ Flood wait: {wait_time}с")
            self.error_count += 1
            self.global_stats['total_errors'] = self.global_stats.get('total_errors', 0) + 1
            await asyncio.sleep(wait_time)
            await self.send_next_command()
            
        except PeerIdInvalidError:
            self.logger.warning("⚠️ Ошибка PeerIdInvalid, обновляем сущность бота...")
            await self.ensure_bot_entity()
            await asyncio.sleep(1)
            await self.send_target_message()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка отправки: {e}")
            self.error_count += 1
            self.global_stats['total_errors'] = self.global_stats.get('total_errors', 0) + 1
            await asyncio.sleep(5)
            await self.send_next_command()


async def main():
    """Главная функция"""
    print("\n" + "="*70)
    print("🚀 МАССОВАЯ РАССЫЛКА В TELEGRAM")
    print("="*70)
    print(f"📁 Папка с сессиями: {SESSIONS_FOLDER}")
    print(f"📄 Файл с сообщением: {MESSAGE_FILE}")
    print("="*70 + "\n")
    
    manager = MultiAccountSender()
    
    if not await manager.initialize_accounts():
        print("\n❌ Не удалось инициализировать ни один аккаунт!")
        print("📁 Проверьте наличие файлов сессий в папке sessions/")
        return
    
    await manager.auto_start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Остановка бота...")
        await manager.stop_all()
        manager.save_stats()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
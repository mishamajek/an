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
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, KeyboardButtonCallback, PeerUser
from telethon.tl.custom import Message
from telethon.tl.functions.messages import StartBotRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest

# Фикс для отображения эмодзи в Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройки (API данные нужно получить на my.telegram.org)
API_ID = 25046122
API_HASH = '58d3e0f528957980a6194874f2479304'

# ID бота
BOT_USERNAME = '@MessageAnonBot'
BOT_USERNAME_WITHOUT_AT = 'MessageAnonBot'

# Папки и файлы
TDATA_FOLDER = 'tdata'  # Папка с tdata
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
os.makedirs(TDATA_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)


# ================== ПОЛНЫЙ СЛОВАРЬ ЭМОДЗИ ==================
EMOJI_DICT = {
    'кот': ['🐱', '😺', '😸', '😻', '😽', '🙀', '😿', '😾', '🐈', '🐆'],
    'котик': ['🐱', '😺', '😸', '😻', '😽', '🙀', '😿', '😾', '🐈', '🐆'],
    'кошка': ['🐱', '😺', '😸', '😻', '😽', '🙀', '😿', '😾', '🐈', '🐆'],
    'собака': ['🐶', '🐕', '🦮', '🐕‍🦺', '🐩'],
    'пес': ['🐶', '🐕', '🦮', '🐕‍🦺', '🐩'],
    'пёс': ['🐶', '🐕', '🦮', '🐕‍🦺', '🐩'],
    'мышь': ['🐭', '🐁', '🐀'],
    'хомяк': ['🐹'],
    'кролик': ['🐰', '🐇'],
    'зайка': ['🐰', '🐇'],
    'лиса': ['🦊'],
    'медведь': ['🐻', '🐻‍❄️'],
    'панда': ['🐼'],
    'тигр': ['🐯', '🐅'],
    'лев': ['🦁', '🐆'],
    'обезьяна': ['🐵', '🐒', '🙈', '🙉', '🙊'],
    'слон': ['🐘'],
    'жираф': ['🦒'],
    'лошадь': ['🐴', '🐎'],
    'корова': ['🐮', '🐄', '🐂'],
    'свинья': ['🐷', '🐖', '🐗'],
    'коза': ['🐐'],
    'овца': ['🐑'],
    'курица': ['🐔', '🐓'],
    'утка': ['🦆'],
    'гусь': ['🦢'],
    'птица': ['🐦', '🦅', '🦉', '🐧'],
    'рыба': ['🐟', '🐠', '🐡', '🐋', '🦈'],
    'дельфин': ['🐬'],
    'кит': ['🐋'],
    'змея': ['🐍'],
    'черепаха': ['🐢'],
    'лягушка': ['🐸'],
    'бабочка': ['🦋'],
    'жук': ['🐞'],
    'яблоко': ['🍎', '🍏'],
    'банан': ['🍌'],
    'виноград': ['🍇'],
    'арбуз': ['🍉'],
    'клубника': ['🍓'],
    'вишня': ['🍒'],
    'персик': ['🍑'],
    'груша': ['🍐'],
    'лимон': ['🍋'],
    'апельсин': ['🍊'],
    'помидор': ['🍅'],
    'огурец': ['🥒'],
    'морковь': ['🥕'],
    'картошка': ['🥔'],
    'гриб': ['🍄'],
    'хлеб': ['🍞'],
    'сыр': ['🧀'],
    'молоко': ['🥛'],
    'яйцо': ['🥚'],
    'пицца': ['🍕'],
    'бургер': ['🍔'],
    'хот-дог': ['🌭'],
    'мороженое': ['🍦', '🍧', '🍨'],
    'торт': ['🍰', '🎂'],
    'пончик': ['🍩'],
    'печенье': ['🍪'],
    'шоколад': ['🍫'],
    'конфета': ['🍬', '🍭'],
    'кофе': ['☕', '🫖'],
    'чай': ['🍵'],
    'вода': ['💧', '🚰'],
    'сок': ['🧃'],
    'пиво': ['🍺', '🍻'],
    'вино': ['🍷'],
    'машина': ['🚗', '🚙', '🚕', '🚓', '🚑', '🚒', '🚌'],
    'автобус': ['🚌', '🚎'],
    'поезд': ['🚂', '🚆', '🚇'],
    'самолёт': ['✈️', '🛩️', '🛫', '🛬'],
    'велосипед': ['🚲', '🚴'],
    'солнце': ['☀️', '☼'],
    'луна': ['🌙', '🌚', '🌛', '🌜'],
    'звезда': ['⭐', '🌟'],
    'облако': ['☁️', '⛅'],
    'дождь': ['🌧️', '☔'],
    'снег': ['❄️', '🌨️', '☃️'],
    'радуга': ['🌈'],
    'сердце': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎'],
    'телефон': ['📱', '📲', '📞', '☎️'],
    'компьютер': ['💻', '🖥️'],
    'деньги': ['💵', '💶', '💷', '💴', '💰', '💳'],
    'ключ': ['🔑', '🗝️'],
    'замок': ['🔒', '🔓'],
    'подарок': ['🎁'],
    'музыка': ['🎵', '🎶', '🎼', '🎤', '🎧', '🎸', '🎹', '🎺', '🎻'],
    'цветок': ['🌸', '🌺', '🌻', '🌼', '🌷', '💐', '🌹'],
    'роза': ['🌹'],
    'дерево': ['🌲', '🌳', '🌴'],
    'океан': ['🌊'],
    'ракета': ['🚀'],
    'галочка': ['✅', '✔️', '☑️'],
    'крестик': ['❌', '✖️', '❎'],
    'лайк': ['👍', '❤️'],
    'дизлайк': ['👎'],
}


class MultiAccountSender:
    """Класс для управления несколькими аккаунтами через tdata"""
    
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
    
    def find_tdata_folders(self) -> List[str]:
        """Находит все папки tdata"""
        folders = []
        if os.path.exists(TDATA_FOLDER):
            for item in os.listdir(TDATA_FOLDER):
                item_path = os.path.join(TDATA_FOLDER, item)
                if os.path.isdir(item_path):
                    folders.append(item)
        return folders
    
    async def initialize_accounts(self):
        tdata_folders = self.find_tdata_folders()
        
        if not tdata_folders:
            print("\n⚠️ Нет папок tdata!")
            print("📁 Положите tdata папки в директорию tdata/")
            print("   (скопируйте их с вашего компьютера через scp)")
            return False
        
        logger.info(f"📁 Найдено tdata папок: {len(tdata_folders)}")
        
        for folder_name in tdata_folders:
            logger.info(f"🔄 Инициализация аккаунта: {folder_name}")
            
            account_log = os.path.join(LOG_FOLDER, f"{folder_name}.log")
            
            # Используем tdata напрямую
            client = TelegramClient(
                os.path.join(TDATA_FOLDER, folder_name),
                API_ID,
                API_HASH
            )
            
            account = AccountSender(
                session_name=folder_name,
                client=client,
                message_text=self.message_text,
                global_stats=self.global_stats,
                log_file=account_log
            )
            
            if await account.initialize():
                self.accounts.append(account)
                logger.info(f"✅ Аккаунт {folder_name} готов к работе")
            else:
                logger.error(f"❌ Не удалось инициализировать аккаунт {folder_name}")
        
        logger.info(f"✅ Готово аккаунтов: {len(self.accounts)} из {len(tdata_folders)}")
        
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
        await self.startup_complete.wait()
        await asyncio.sleep(3)
        
        if not self.accounts:
            logger.error("❌ Нет активных аккаунтов для автоматического запуска")
            return
        
        logger.info("="*70)
        logger.info("🤖 АВТОМАТИЧЕСКИЙ ЗАПУСК РАССЫЛКИ")
        logger.info(f"📊 Аккаунтов: {len(self.accounts)}")
        logger.info("="*70)
        
        await self.start_all()


class AccountSender:
    """Класс для отдельного аккаунта с tdata"""
    
    def __init__(self, session_name: str, client: TelegramClient, message_text: str, 
                 global_stats: dict, log_file: str):
        self.session_name = session_name
        self.client = client
        self.message_text = message_text
        self.global_stats = global_stats
        
        self.logger = logging.getLogger(f"Account_{session_name}")
        self.logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        self.bot_entity = None
        self.waiting_for_next = False
        self.sending_enabled = False
        self.send_count = 0
        self.error_count = 0
        self.running = True
        self.registered = False
        self.registration_step = 0
        self.reconnect_attempts = 0
        self.registration_complete = False
        
        self.last_next_command_time = 0
        self.next_command_cooldown = 5
        self.processing_captcha = False
        self.too_many_requests_cooldown = 300
        
        self.captcha_stats = {
            'solved': 0,
            'failed': 0,
            'unknown': defaultdict(int)
        }
        
        self.debug_mode = True
        self.last_processed_message_id = None
        
    async def initialize(self) -> bool:
        try:
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                self.logger.warning(f"⚠️ Аккаунт {self.session_name} не авторизован")
                return False
            
            me = await self.client.get_me()
            if me:
                self.logger.info(f"✅ Авторизован как: {me.first_name} (ID: {me.id})")
            
            # Находим бота
            await self.get_bot_entity()
            
            if not self.bot_entity:
                self.logger.error(f"❌ Бот {BOT_USERNAME} не найден")
                return False
            
            # Регистрируем обработчик сообщений
            @self.client.on(events.NewMessage)
            async def handler(event):
                await self.handle_bot_message(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def get_bot_entity(self):
        """Находит бота через диалоги или поиск"""
        try:
            # Сначала ищем в диалогах
            async for dialog in self.client.iter_dialogs():
                if dialog.is_user and dialog.entity and hasattr(dialog.entity, 'username'):
                    username = dialog.entity.username or ''
                    if 'MessageAnonBot' in username or 'messageanon' in username.lower():
                        self.bot_entity = dialog.entity
                        self.logger.info(f"✅ Бот найден в диалогах: @{username}")
                        return
        except Exception as e:
            self.logger.warning(f"Поиск в диалогах: {e}")
        
        # Пробуем найти через get_entity
        try:
            self.bot_entity = await self.client.get_entity(BOT_USERNAME)
            self.logger.info(f"✅ Бот найден через get_entity")
            return
        except Exception as e:
            self.logger.warning(f"get_entity не сработал: {e}")
        
        # Пробуем через ResolveUsername
        try:
            result = await self.client(functions.contacts.ResolveUsernameRequest(BOT_USERNAME_WITHOUT_AT))
            self.bot_entity = result.peer
            self.logger.info(f"✅ Бот найден через ResolveUsername")
            return
        except Exception as e:
            self.logger.warning(f"ResolveUsername не сработал: {e}")
        
        self.logger.error("❌ Бот не найден")
    
    async def ensure_bot_entity(self):
        if self.bot_entity is None:
            await self.get_bot_entity()
        return self.bot_entity is not None
    
    async def start_bot_dialog(self):
        """Запускает диалог с ботом и проходит регистрацию"""
        if not await self.ensure_bot_entity():
            return False
        
        try:
            # Отправляем /start
            await self.client.send_message(self.bot_entity, '/start')
            self.logger.info("📤 Отправлен /start")
            await asyncio.sleep(2)
            
            # Получаем последнее сообщение
            async for msg in self.client.iter_messages(self.bot_entity, limit=1):
                if msg.text:
                    self.logger.info(f"📩 Ответ бота: {msg.text[:100]}")
                    
                    # Проверяем, нужно ли проходить регистрацию
                    if 'пол' in msg.text.lower() or 'регистрация' in msg.text.lower() or 'выбери' in msg.text.lower():
                        self.logger.info("🔘 Начинаем регистрацию...")
                        return await self.handle_registration_message(msg)
                    else:
                        self.logger.info("✅ Регистрация не требуется")
                        self.registration_complete = True
                        return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска диалога: {e}")
            return False
    
    async def handle_registration_message(self, msg):
        """Обрабатывает регистрационное сообщение"""
        try:
            message_text = msg.text
            print(f"\n📝 [{self.session_name}] РЕГИСТРАЦИЯ:")
            print(f"Текст: {message_text[:200]}")
            
            # Шаг 1: Выбор пола
            if 'пол' in message_text.lower() or 'выбери' in message_text.lower():
                if msg.reply_markup:
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            if hasattr(button, 'text'):
                                btn_text = button.text
                                if 'мужской' in btn_text.lower() or 'муж' in btn_text.lower():
                                    print(f"🔘 [{self.session_name}] Выбираю: {btn_text}")
                                    await msg.click(text=btn_text)
                                    await asyncio.sleep(2)
                                    
                                    # После выбора пола ждем вопрос о возрасте
                                    async for new_msg in self.client.iter_messages(self.bot_entity, limit=1):
                                        if new_msg.text and ('возраст' in new_msg.text.lower() or 'лет' in new_msg.text.lower()):
                                            age = '25'  # Отправляем возраст
                                            print(f"🔢 [{self.session_name}] Отправляю возраст: {age}")
                                            await self.client.send_message(self.bot_entity, age)
                                            await asyncio.sleep(2)
                                            self.registration_complete = True
                                            print(f"✅ [{self.session_name}] Регистрация завершена!")
                                            return True
                                    break
                                elif 'женский' in btn_text.lower() or 'жен' in btn_text.lower():
                                    print(f"🔘 [{self.session_name}] Выбираю: {btn_text}")
                                    await msg.click(text=btn_text)
                                    await asyncio.sleep(2)
                                    
                                    async for new_msg in self.client.iter_messages(self.bot_entity, limit=1):
                                        if new_msg.text and ('возраст' in new_msg.text.lower() or 'лет' in new_msg.text.lower()):
                                            age = '25'
                                            print(f"🔢 [{self.session_name}] Отправляю возраст: {age}")
                                            await self.client.send_message(self.bot_entity, age)
                                            await asyncio.sleep(2)
                                            self.registration_complete = True
                                            print(f"✅ [{self.session_name}] Регистрация завершена!")
                                            return True
                                    break
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка регистрации: {e}")
            return False
    
    async def run(self):
        if not self.sending_enabled:
            self.sending_enabled = True
            self.waiting_for_next = False
            self.last_next_command_time = 0
            self.registration_complete = False
            self.reconnect_attempts = 0
            
            # Запускаем диалог с ботом и проходим регистрацию
            self.logger.info("🚀 Запуск бота...")
            await self.start_bot_dialog()
            
            if not self.registration_complete:
                self.logger.warning("⚠️ Регистрация не завершена, пробуем еще раз...")
                await asyncio.sleep(3)
                await self.start_bot_dialog()
            
            self.logger.info("🚀 Рассылка запущена")
            await self.send_next_command()
    
    def stop(self):
        self.sending_enabled = False
        self.waiting_for_next = False
        self.logger.info("⏸️ Рассылка остановлена")
    
    async def send_next_command(self):
        if not self.sending_enabled or not self.bot_entity:
            return
        
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
            self.reconnect_attempts = 0
            
        except FloodWaitError as e:
            wait_time = e.seconds
            self.logger.warning(f"⚠️ Flood wait: {wait_time}с")
            self.error_count += 1
            self.global_stats['total_errors'] = self.global_stats.get('total_errors', 0) + 1
            await asyncio.sleep(wait_time)
            await self.send_next_command()
            
        except PeerIdInvalidError:
            self.logger.warning("⚠️ Ошибка PeerIdInvalid, обновляем сущность бота...")
            await self.get_bot_entity()
            await asyncio.sleep(2)
            await self.send_next_command()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка /next: {e}")
            self.error_count += 1
            self.global_stats['total_errors'] = self.global_stats.get('total_errors', 0) + 1
            self.reconnect_attempts += 1
            
            if self.reconnect_attempts > 5:
                self.logger.error("Слишком много ошибок, пауза 60 секунд...")
                await asyncio.sleep(60)
                self.reconnect_attempts = 0
            
            await asyncio.sleep(5)
            await self.send_next_command()
    
    def extract_target_name(self, text):
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
        
        # Если регистрация не завершена, обрабатываем регистрационные сообщения
        if not self.registration_complete:
            if message_text and ('пол' in message_text.lower() or 'возраст' in message_text.lower() or 'выбери' in message_text.lower()):
                if event.message.reply_markup or 'выбери' in message_text.lower():
                    print(f"🔘 [{self.session_name}] Обнаружена регистрация")
                    await self.start_bot_dialog()
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
        if not self.bot_entity:
            await self.get_bot_entity()
        
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
            await self.get_bot_entity()
            await asyncio.sleep(2)
            await self.send_target_message()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка отправки: {e}")
            self.error_count += 1
            self.global_stats['total_errors'] = self.global_stats.get('total_errors', 0) + 1
            await asyncio.sleep(5)
            await self.send_next_command()


async def main():
    print("\n" + "="*70)
    print("🚀 МАССОВАЯ РАССЫЛКА В TELEGRAM (TDATA)")
    print("="*70)
    print(f"📁 Папка с tdata: {TDATA_FOLDER}")
    print(f"📄 Файл с сообщением: {MESSAGE_FILE}")
    print("="*70 + "\n")
    
    manager = MultiAccountSender()
    
    if not await manager.initialize_accounts():
        print("\n❌ Не удалось инициализировать ни один аккаунт!")
        print("📁 Проверьте наличие папок tdata в директории tdata/")
        print("   (скопируйте их с вашего компьютера через scp)")
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
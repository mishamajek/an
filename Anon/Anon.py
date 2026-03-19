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
from telethon.errors import FloodWaitError, SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# Фикс для отображения эмодзи в Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройки (API данные нужно получить на my.telegram.org)
API_ID = 25046122  # Замените на свой api_id
API_HASH = '58d3e0f528957980a6194874f2479304'  # Замените на свой api_hash

# ID бота
BOT_USERNAME = '@MessageAnonBot'

# Папки и файлы
SESSIONS_FOLDER = 'sessions'  # Папка с файлами сессий
MESSAGE_FILE = 'message.txt'  # Файл с текстом рассылки
LOG_FOLDER = 'logs'  # Папка для логов
STATS_FILE = 'stats.json'  # Файл с общей статистикой

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
EMOJI_DICT = {
    # Животные
    'кот': ['🐱', '😺', '😸', '😻', '😽', '🙀', '😿', '😾', '🐈', '🐆'],
    'коты': ['🐱', '😺', '😸', '😻', '😽', '🙀', '😿', '😾', '🐈', '🐆'],
    'котик': ['🐱', '😺', '😸', '😻', '😽', '🙀', '😿', '😾', '🐈', '🐆'],
    'котёнок': ['🐱', '😺', '😸', '😻', '😽', '🙀', '😿', '😾', '🐈', '🐆'],
    'кошка': ['🐱', '😺', '😸', '😻', '😽', '🙀', '😿', '😾', '🐈', '🐆'],
    'кошечка': ['🐱', '😺', '😸', '😻', '😽', '🙀', '😿', '😾', '🐈', '🐆'],
    'собака': ['🐶', '🐕', '🦮', '🐕‍🦺', '🐩'],
    'пёс': ['🐶', '🐕', '🦮', '🐕‍🦺', '🐩'],
    'пес': ['🐶', '🐕', '🦮', '🐕‍🦺', '🐩'],
    'собачка': ['🐶', '🐕', '🦮', '🐕‍🦺', '🐩'],
    'псина': ['🐶', '🐕', '🦮', '🐕‍🦺', '🐩'],
    'мышь': ['🐭', '🐁', '🐀'],
    'мышка': ['🐭', '🐁', '🐀'],
    'хомяк': ['🐹'],
    'хомячок': ['🐹'],
    'кролик': ['🐰', '🐇'],
    'заяц': ['🐰', '🐇'],
    'зайка': ['🐰', '🐇'],
    'лиса': ['🦊'],
    'лисичка': ['🦊'],
    'медведь': ['🐻', '🐻‍❄️'],
    'мишка': ['🐻', '🐻‍❄️'],
    'панда': ['🐼'],
    'коала': ['🐨'],
    'тигр': ['🐯', '🐅'],
    'тигренок': ['🐯', '🐅'],
    'лев': ['🦁', '🐆'],
    'львенок': ['🦁', '🐆'],
    'обезьяна': ['🐵', '🐒', '🙈', '🙉', '🙊'],
    'мартышка': ['🐵', '🐒', '🙈', '🙉', '🙊'],
    'слон': ['🐘'],
    'слоник': ['🐘'],
    'жираф': ['🦒'],
    'зебра': ['🦓'],
    'бегемот': ['🦛'],
    'носорог': ['🦏'],
    'верблюд': ['🐫', '🐪'],
    'лошадь': ['🐴', '🐎', '🏇'],
    'конь': ['🐴', '🐎'],
    'лошадка': ['🐴', '🐎', '🏇'],
    'корова': ['🐮', '🐄', '🐂'],
    'бык': ['🐂'],
    'коровка': ['🐮', '🐄', '🐂'],
    'свинья': ['🐷', '🐖', '🐗'],
    'поросёнок': ['🐷', '🐖'],
    'свинка': ['🐷', '🐖', '🐗'],
    'коза': ['🐐'],
    'козлик': ['🐐'],
    'овца': ['🐑'],
    'овечка': ['🐑'],
    'баран': ['🐏'],
    'курица': ['🐔', '🐓'],
    'петух': ['🐓'],
    'цыплёнок': ['🐥', '🐤', '🐣'],
    'цыпа': ['🐥', '🐤', '🐣'],
    'утка': ['🦆'],
    'уточка': ['🦆'],
    'гусь': ['🦢'],
    'гусенок': ['🦢'],
    'лебедь': ['🦢'],
    'голубь': ['🕊️'],
    'воробей': ['🐦'],
    'птица': ['🐦', '🦅', '🦉', '🐧'],
    'птичка': ['🐦', '🦅', '🦉', '🐧'],
    'орёл': ['🦅'],
    'орел': ['🦅'],
    'сова': ['🦉'],
    'совенок': ['🦉'],
    'пингвин': ['🐧'],
    'рыба': ['🐟', '🐠', '🐡', '🐋', '🦈'],
    'рыбка': ['🐟', '🐠', '🐡', '🐋', '🦈'],
    'дельфин': ['🐬'],
    'кит': ['🐋'],
    'китенок': ['🐋'],
    'акула': ['🦈'],
    'змея': ['🐍'],
    'змейка': ['🐍'],
    'ящерица': ['🦎'],
    'черепаха': ['🐢'],
    'черепашка': ['🐢'],
    'лягушка': ['🐸'],
    'жаба': ['🐸'],
    'крокодил': ['🐊'],
    'динозавр': ['🦕', '🦖'],
    'паук': ['🕷️', '🕸️'],
    'паучок': ['🕷️', '🕸️'],
    'насекомое': ['🐜', '🐝', '🐞', '🦋', '🐛'],
    'муравей': ['🐜'],
    'пчела': ['🐝'],
    'пчелка': ['🐝'],
    'бабочка': ['🦋'],
    'жук': ['🐞'],
    'улитка': ['🐌'],
    
    # Еда
    'яблоко': ['🍎', '🍏'],
    'яблочко': ['🍎', '🍏'],
    'банан': ['🍌'],
    'бананчик': ['🍌'],
    'виноград': ['🍇'],
    'арбуз': ['🍉'],
    'арбузик': ['🍉'],
    'дыня': ['🍈'],
    'дынька': ['🍈'],
    'клубника': ['🍓'],
    'клубничка': ['🍓'],
    'малина': ['🍓'],
    'вишня': ['🍒'],
    'вишенка': ['🍒'],
    'персик': ['🍑'],
    'груша': ['🍐'],
    'грушка': ['🍐'],
    'лимон': ['🍋'],
    'лимончик': ['🍋'],
    'апельсин': ['🍊'],
    'мандарин': ['🍊'],
    'помидор': ['🍅'],
    'помидорка': ['🍅'],
    'огурец': ['🥒'],
    'огурчик': ['🥒'],
    'морковь': ['🥕'],
    'морковка': ['🥕'],
    'картошка': ['🥔'],
    'картофель': ['🥔'],
    'брокколи': ['🥦'],
    'гриб': ['🍄'],
    'грибок': ['🍄'],
    'хлеб': ['🍞'],
    'хлебушек': ['🍞'],
    'сыр': ['🧀'],
    'сырок': ['🧀'],
    'молоко': ['🥛'],
    'яйцо': ['🥚'],
    'яичко': ['🥚'],
    'пицца': ['🍕'],
    'бургер': ['🍔'],
    'гамбургер': ['🍔'],
    'хот-дог': ['🌭'],
    'сэндвич': ['🥪'],
    'суши': ['🍣'],
    'роллы': ['🍣'],
    'мороженое': ['🍦', '🍧', '🍨'],
    'торт': ['🍰', '🎂'],
    'тортик': ['🍰', '🎂'],
    'пирожное': ['🧁'],
    'пончик': ['🍩'],
    'печенье': ['🍪'],
    'печенька': ['🍪'],
    'шоколад': ['🍫'],
    'шоколадка': ['🍫'],
    'конфета': ['🍬', '🍭'],
    'конфетка': ['🍬', '🍭'],
    'леденец': ['🍭'],
    'кекс': ['🧁'],
    'кофе': ['☕', '🫖'],
    'кофеек': ['☕', '🫖'],
    'чай': ['🍵'],
    'чаек': ['🍵'],
    'вода': ['💧', '🚰'],
    'водичка': ['💧', '🚰'],
    'сок': ['🧃'],
    'пиво': ['🍺', '🍻'],
    'пивко': ['🍺', '🍻'],
    'вино': ['🍷'],
    'винцо': ['🍷'],
    'коктейль': ['🍸', '🍹'],
    
    # Транспорт
    'машина': ['🚗', '🚙', '🚕', '🚓', '🚑', '🚒', '🚌', '🚎'],
    'автомобиль': ['🚗', '🚙', '🚕', '🚓', '🚑', '🚒', '🚌', '🚎'],
    'машинка': ['🚗', '🚙', '🚕', '🚓', '🚑', '🚒', '🚌', '🚎'],
    'такси': ['🚕'],
    'таксофон': ['🚕'],
    'полиция': ['🚓'],
    'полицейская машина': ['🚓'],
    'скорая': ['🚑'],
    'скорая помощь': ['🚑'],
    'пожарная': ['🚒'],
    'пожарная машина': ['🚒'],
    'автобус': ['🚌', '🚎'],
    'троллейбус': ['🚎'],
    'трамвай': ['🚋', '🚊'],
    'поезд': ['🚂', '🚆', '🚇', '🚈'],
    'поездка': ['🚂', '🚆', '🚇', '🚈'],
    'метро': ['🚇'],
    'самолёт': ['✈️', '🛩️', '🛫', '🛬'],
    'самолет': ['✈️', '🛩️', '🛫', '🛬'],
    'вертолёт': ['🚁'],
    'вертолет': ['🚁'],
    'кораблик': ['🚢', '⛵', '🛥️', '🚤'],
    'лодка': ['⛵', '🛶'],
    'велосипед': ['🚲', '🚴'],
    'велик': ['🚲', '🚴'],
    'мотоцикл': ['🏍️'],
    'грузовик': ['🚚', '🚛', '🚜'],
    
    # Спорт
    'футбол': ['⚽'],
    'мяч': ['⚽', '🏀', '🏐', '🏈', '⚾', '🎾'],
    'баскетбол': ['🏀'],
    'волейбол': ['🏐'],
    'теннис': ['🎾'],
    'бейсбол': ['⚾'],
    'гольф': ['⛳'],
    'хоккей': ['🏒'],
    'лыжи': ['⛷️'],
    'сноуборд': ['🏂'],
    'коньки': ['⛸️'],
    'плавание': ['🏊'],
    'бокс': ['🥊'],
    'карате': ['🥋'],
    
    # Погода
    'солнце': ['☀️', '☼'],
    'солнышко': ['☀️', '☼'],
    'луна': ['🌙', '🌚', '🌛', '🌜'],
    'месяц': ['🌙', '🌚', '🌛', '🌜'],
    'звезда': ['⭐', '🌟'],
    'звездочка': ['⭐', '🌟'],
    'облако': ['☁️', '⛅'],
    'облачко': ['☁️', '⛅'],
    'туча': ['☁️', '🌧️'],
    'тучка': ['☁️', '🌧️'],
    'дождь': ['🌧️', '☔'],
    'дождик': ['🌧️', '☔'],
    'снег': ['❄️', '🌨️', '☃️'],
    'снежок': ['❄️', '🌨️', '☃️'],
    'гроза': ['⛈️', '🌩️'],
    'радуга': ['🌈'],
    'ветер': ['💨'],
    'ветерок': ['💨'],
    'туман': ['🌫️'],
    
    # Флаги
    'флаг': ['🚩', '🎌'],
    'россия': ['🇷🇺'],
    'сша': ['🇺🇸'],
    'китай': ['🇨🇳'],
    'япония': ['🇯🇵'],
    
    # Эмоции
    'улыбка': ['😊', '😃', '😄', '😁', '😆', '🙂', '😀'],
    'смайлик': ['😊', '😃', '😄', '😁', '😆', '🙂', '😀'],
    'грусть': ['😢', '😭', '😞', '😔', '😟'],
    'печаль': ['😢', '😭', '😞', '😔', '😟'],
    'гнев': ['😠', '😡', '🤬'],
    'злость': ['😠', '😡', '🤬'],
    'смех': ['😂', '🤣', '😆'],
    'любовь': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎'],
    'сердце': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎'],
    'сердечко': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎'],
    
    # Предметы
    'книга': ['📕', '📗', '📘', '📙', '📚', '📖'],
    'книжка': ['📕', '📗', '📘', '📙', '📚', '📖'],
    'ручка': ['✒️', '🖊️', '🖋️'],
    'карандаш': ['✏️'],
    'телефон': ['📱', '📲', '📞', '☎️'],
    'трубка': ['📞', '☎️'],
    'компьютер': ['💻', '🖥️'],
    'ноутбук': ['💻'],
    'телевизор': ['📺'],
    'часы': ['⏰', '⌚', '🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛'],
    'деньги': ['💵', '💶', '💷', '💴', '💰', '💳'],
    'ключ': ['🔑', '🗝️'],
    'замок': ['🔒', '🔓'],
    'лампа': ['💡'],
    'лампочка': ['💡'],
    'свеча': ['🕯️'],
    'огонь': ['🔥'],
    'лёд': ['🧊'],
    'лед': ['🧊'],
    'шар': ['🎈'],
    'шарик': ['🎈'],
    'подарок': ['🎁'],
    'колокольчик': ['🔔'],
    'музыка': ['🎵', '🎶', '🎼', '🎤', '🎧', '🎷', '🎸', '🎹', '🎺', '🎻'],
    'гитара': ['🎸'],
    'пианино': ['🎹'],
    'барабан': ['🥁'],
    
    # Природа
    'цветок': ['🌸', '🌺', '🌻', '🌼', '🌷', '💐', '🌹'],
    'цветочек': ['🌸', '🌺', '🌻', '🌼', '🌷', '💐', '🌹'],
    'роза': ['🌹'],
    'розочка': ['🌹'],
    'дерево': ['🌲', '🌳', '🌴'],
    'деревце': ['🌲', '🌳', '🌴'],
    'ёлка': ['🎄'],
    'ель': ['🎄'],
    'елочка': ['🎄'],
    'трава': ['🌿', '☘️'],
    'травка': ['🌿', '☘️'],
    'лист': ['🍃', '🍂', '🍁'],
    'листик': ['🍃', '🍂', '🍁'],
    'камень': ['🪨'],
    'камешек': ['🪨'],
    'гора': ['⛰️', '🏔️'],
    'горка': ['⛰️', '🏔️'],
    'вулкан': ['🌋'],
    'океан': ['🌊'],
    'волна': ['🌊'],
    'волны': ['🌊'],
    'море': ['🌊'],
    
    # Космос
    'планета': ['🌍', '🌎', '🌏', '🪐'],
    'земля': ['🌍', '🌎', '🌏'],
    'земной шар': ['🌍', '🌎', '🌏'],
    'ракета': ['🚀'],
    'спутник': ['🛰️'],
    'нло': ['🛸'],
    'тарелка': ['🛸'],
    
    # Разное
    'знак вопроса': ['❓', '❔'],
    'вопрос': ['❓', '❔'],
    'вопросительный знак': ['❓', '❔'],
    'восклицательный знак': ['❗', '❕'],
    'галочка': ['✅', '✔️', '☑️'],
    'крестик': ['❌', '✖️', '❎'],
    'стоп': ['🛑'],
    'опасность': ['⚠️', '☢️', '☣️'],
    'запрещено': ['🚫', '⛔'],
    'инфо': ['ℹ️', '🛈'],
    'информация': ['ℹ️', '🛈'],
    'подсказка': ['💡'],
    'идея': ['💡'],
    'лайк': ['👍', '❤️'],
    'дизлайк': ['👎'],
    'ок': ['👌', '🆗'],
    'круто': ['🔥', '💯'],
    'супер': ['🔥', '💯'],
}

class MultiAccountSender:
    """Класс для управления несколькими аккаунтами"""
    
    def __init__(self):
        self.accounts: List['AccountSender'] = []
        self.message_text = self.load_message()
        self.running = True
        self.global_stats = self.load_stats()
        
    def load_message(self) -> str:
        """Загружает сообщение из файла message.txt"""
        try:
            if os.path.exists(MESSAGE_FILE):
                with open(MESSAGE_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        logger.info(f"✅ Загружено сообщение из {MESSAGE_FILE}")
                        return content
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки сообщения: {e}")
        
        # Сообщение по умолчанию
        default_msg = """Привет! Это тестовое сообщение.

Оно может содержать несколько абзацев.
И даже эмодзи! 🎉✨

С уважением,
Отправитель"""
        
        # Сохраняем сообщение по умолчанию в файл
        try:
            with open(MESSAGE_FILE, 'w', encoding='utf-8') as f:
                f.write(default_msg)
            logger.info(f"✅ Создан файл {MESSAGE_FILE} с сообщением по умолчанию")
        except:
            pass
        
        return default_msg
    
    def load_stats(self) -> dict:
        """Загружает общую статистику"""
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'total_sent': 0, 'total_errors': 0, 'captcha_solved': 0, 'captcha_failed': 0}
    
    def save_stats(self):
        """Сохраняет общую статистику"""
        try:
            with open(STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.global_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения статистики: {e}")
    
    def find_session_files(self) -> List[str]:
        """Находит все файлы сессий в папке sessions"""
        session_files = []
        
        # Ищем файлы с расширением .session
        for file in glob.glob(os.path.join(SESSIONS_FOLDER, "*.session")):
            session_name = os.path.splitext(os.path.basename(file))[0]
            session_files.append(session_name)
        
        return session_files
    
    async def initialize_accounts(self):
        """Инициализирует все аккаунты"""
        session_names = self.find_session_files()
        
        if not session_names:
            logger.warning("⚠️ В папке sessions нет файлов сессий!")
            logger.info("📁 Создайте файлы сессий в папке sessions или добавьте существующие")
            return False
        
        logger.info(f"📁 Найдено {len(session_names)} файлов сессий")
        
        for session_name in session_names:
            logger.info(f"🔄 Инициализация аккаунта: {session_name}")
            
            # Создаем отдельный лог-файл для каждого аккаунта
            account_log = os.path.join(LOG_FOLDER, f"{session_name}.log")
            
            # Создаем клиента
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
            
            # Пытаемся подключиться и авторизоваться
            if await account.initialize():
                self.accounts.append(account)
                logger.info(f"✅ Аккаунт {session_name} готов к работе")
            else:
                logger.error(f"❌ Не удалось инициализировать аккаунт {session_name}")
        
        logger.info(f"✅ Готово аккаунтов: {len(self.accounts)} из {len(session_names)}")
        return len(self.accounts) > 0
    
    async def start_all(self):
        """Запускает рассылку на всех аккаунтах"""
        logger.info(f"🚀 Запуск рассылки на {len(self.accounts)} аккаунтах")
        
        # Запускаем все аккаунты одновременно
        tasks = [account.run() for account in self.accounts]
        await asyncio.gather(*tasks)
    
    async def stop_all(self):
        """Останавливает все аккаунты"""
        logger.info("⏸️ Остановка всех аккаунтов...")
        for account in self.accounts:
            account.stop()
    
    async def process_commands(self):
        """Обработка команд из консоли"""
        print("\n" + "="*70)
        print("🚀 МАССОВАЯ РАССЫЛКА С НЕСКОЛЬКИХ АККАУНТОВ")
        print("="*70)
        print(f"📁 Папка с сессиями: {SESSIONS_FOLDER}")
        print(f"📄 Файл с сообщением: {MESSAGE_FILE}")
        print(f"📊 Аккаунтов загружено: {len(self.accounts)}")
        print("\n📋 КОМАНДЫ:")
        print("  /start - запустить рассылку на всех аккаунтах")
        print("  /stop - остановить рассылку")
        print("  /status - статус всех аккаунтов")
        print("  /message - показать текущее сообщение")
        print("  /stats - общая статистика")
        print("  /exit - выход")
        print("="*70 + "\n")
        
        while self.running:
            try:
                command = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input(">>> ").strip().lower()
                )
                
                if command == '/start':
                    logger.info("🚀 Запуск рассылки...")
                    asyncio.create_task(self.start_all())
                    
                elif command == '/stop':
                    logger.info("⏸️ Остановка рассылки...")
                    await self.stop_all()
                    
                elif command == '/status':
                    self.show_status()
                    
                elif command == '/message':
                    print("\n📄 ТЕКУЩЕЕ СООБЩЕНИЕ:")
                    print("="*70)
                    print(self.message_text)
                    print("="*70)
                    print(f"📊 Длина: {len(self.message_text)} символов")
                    
                elif command == '/stats':
                    self.show_stats()
                    
                elif command == '/exit':
                    print("👋 Завершение работы...")
                    self.running = False
                    await self.stop_all()
                    
                    # Отключаем всех клиентов
                    for account in self.accounts:
                        await account.client.disconnect()
                    
                    self.save_stats()
                    sys.exit(0)
                    
            except Exception as e:
                logger.error(f"Ошибка команды: {e}")
    
    def show_status(self):
        """Показывает статус всех аккаунтов"""
        print("\n" + "="*70)
        print("📊 СТАТУС АККАУНТОВ")
        print("="*70)
        
        active = sum(1 for a in self.accounts if a.sending_enabled)
        waiting = sum(1 for a in self.accounts if a.waiting_for_next)
        
        print(f"📁 Всего аккаунтов: {len(self.accounts)}")
        print(f"✅ Активных: {active}")
        print(f"⏳ Ожидают ответа: {waiting}")
        print()
        
        for account in self.accounts:
            status = "✅" if account.sending_enabled else "⏸️"
            waiting = "⏳" if account.waiting_for_next else "   "
            print(f"  {status} {waiting} {account.session_name}: {account.send_count} отправлено")
        
        print("="*70 + "\n")
    
    def show_stats(self):
        """Показывает общую статистику"""
        total_sent = sum(a.send_count for a in self.accounts)
        total_errors = sum(a.error_count for a in self.accounts)
        captcha_solved = sum(a.captcha_stats['solved'] for a in self.accounts)
        captcha_failed = sum(a.captcha_stats['failed'] for a in self.accounts)
        
        print("\n" + "="*70)
        print("📊 ОБЩАЯ СТАТИСТИКА")
        print("="*70)
        print(f"✅ Отправлено сообщений: {total_sent}")
        print(f"❌ Ошибок: {total_errors}")
        print(f"🔄 Капч решено: {captcha_solved}")
        print(f"❓ Капч не решено: {captcha_failed}")
        print(f"📈 Процент успеха капчи: {captcha_solved/(captcha_solved+captcha_failed)*100:.1f}%" if captcha_solved+captcha_failed > 0 else "📈 Процент успеха капчи: N/A")
        print("="*70 + "\n")


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
        
        # Последний обработанный message_id для защиты от дубликатов
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
    
    async def run(self):
        """Запускает рассылку на аккаунте"""
        if not self.sending_enabled:
            self.sending_enabled = True
            self.waiting_for_next = False
            self.last_next_command_time = 0
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
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка /next: {e}")
            self.error_count += 1
            self.global_stats['total_errors'] = self.global_stats.get('total_errors', 0) + 1
            await asyncio.sleep(5)
            await self.send_next_command()
    
    def extract_target_name(self, text):
        """Извлекает название из текста капчи"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        if self.debug_mode:
            print(f"🔍 [DEBUG {self.session_name}] Анализируем текст капчи")
        
        # СПЕЦИАЛЬНЫЙ ПАТТЕРН ДЛЯ "изображн(а) Х"
        match = re.search(r'изображн\(а\)\s+([а-яё]+)', text_lower)
        if match:
            found = match.group(1)
            found = re.sub(r'[.,!?:;()]', '', found)
            return found
        
        # Паттерн для "изображен(а) Х"
        match = re.search(r'изображен\(а\)\s+([а-яё]+)', text_lower)
        if match:
            found = match.group(1)
            found = re.sub(r'[.,!?:;()]', '', found)
            return found
        
        # Паттерн для "где Х"
        match = re.search(r'где\s+([а-яё]+)', text_lower)
        if match:
            found = match.group(1)
            found = re.sub(r'[.,!?:;()]', '', found)
            return found
        
        # Если не нашли по паттернам, ищем просто слово после "кнопку"
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
            target_name = self.extract_target_name(message_text)
            
            if not target_name:
                self.logger.error("❌ Не удалось определить, что нужно найти в капче")
                self.captcha_stats['failed'] += 1
                self.global_stats['captcha_failed'] = self.global_stats.get('captcha_failed', 0) + 1
                return False
            
            self.logger.info(f"🔍 В капче нужно найти: {target_name}")
            
            if not event.message.reply_markup or not event.message.reply_markup.rows:
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
            
            # Пробуем нажать на кнопку
            captcha_solved = False
            
            # Способ 1: через событие по тексту
            try:
                await event.click(text=target_button.text)
                captcha_solved = True
            except:
                pass
            
            # Способ 2: через данные кнопки
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
                
                # Отправляем /next после решения капчи
                if self.sending_enabled:
                    await asyncio.sleep(2)
                    await self.send_next_command()
                
                return True
            else:
                self.logger.error("❌ Не удалось решить капчу")
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
        
        # Защита от дубликатов
        message_id = event.message.id
        if self.last_processed_message_id == message_id:
            return
        self.last_processed_message_id = message_id
        
        message_text = event.raw_text
        
        # Проверка на ошибку "слишком много запросов"
        if message_text and ("слишком много запросов" in message_text.lower() or 
                             "too many requests" in message_text.lower()):
            self.logger.warning("⚠️ Обнаружена ошибка 'Слишком много запросов'!")
            self.logger.info(f"⏳ Ожидание {self.too_many_requests_cooldown // 60} минут...")
            
            await asyncio.sleep(self.too_many_requests_cooldown)
            
            if self.sending_enabled:
                await self.send_next_command()
            
            return
        
        # Обработка капчи
        if message_text and ("проверку на робота" in message_text or 
                             "капча" in message_text.lower() or
                             "нажми на кнопку" in message_text):
            
            if event.message.reply_markup and event.message.reply_markup.rows:
                self.logger.warning("⚠️ Обнаружена капча!")
                await self.handle_captcha(event)
                return
        
        if self.waiting_for_next:
            if self.check_for_image(event):
                self.waiting_for_next = False
                self.logger.info("✅ Получено подтверждение (изображение)!")
                
                # Отправляем целевое сообщение
                await asyncio.sleep(1.5)
                await self.send_target_message()


    async def send_target_message(self):
        """Отправка целевого сообщения"""
        try:
            await self.client.send_message(self.bot_entity, self.message_text)
            self.logger.info(f"✅ Сообщение #{self.send_count} отправлено!")
            
            await asyncio.sleep(3)
            await self.send_next_command()
            
        except FloodWaitError as e:
            wait_time = e.seconds
            self.logger.warning(f"⚠️ Flood wait: {wait_time}с")
            self.error_count += 1
            self.global_stats['total_errors'] = self.global_stats.get('total_errors', 0) + 1
            await asyncio.sleep(wait_time)
            await self.send_next_command()
            
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
    
    # Создаем менеджер аккаунтов
    manager = MultiAccountSender()
    
    # Инициализируем аккаунты
    if not await manager.initialize_accounts():
        print("\n❌ Не удалось инициализировать ни один аккаунт!")
        print("📁 Проверьте наличие файлов сессий в папке sessions/")
        return
    
    # Запускаем обработку команд
    await manager.process_commands()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
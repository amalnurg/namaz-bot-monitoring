#!/usr/bin/env python3
"""
Микросервис для напоминаний о дуа
Запуск: python3 dua_bot.py
"""

import requests
import logging
from datetime import datetime, timezone, timedelta
import time
import json
import os
import random

# ==================== НАСТРОЙКИ ====================
TELEGRAM_BOT_TOKEN = "8397802323:AAEIVNDvG0UWq9mdyA5gqlrPVjycFRanzCI"
TELEGRAM_CHAT_ID = "1959373637"

# Время напоминаний (по UTC+5 - Уфа)
DUA_TIMES = [
    {"name": "Утреннее дуа", "time": "07:00", "emoji": "🌅"},
    {"name": "Дневное дуа", "time": "14:00", "emoji": "☀️"},
    {"name": "Вечернее дуа", "time": "20:00", "emoji": "🌙"}
]

# База дуа (можно расширять)
DUA_DATABASE = [
    "Субханаллах (Слава Аллаху) - 33 раза",
    "Альхамдулиллях (Хвала Аллаху) - 33 раза",
    "Аллаху Акбар (Аллах Велик) - 34 раза",
    "Раббана атина фид-дунья хасанатан ва филь-ахирати хасанатан ва кына 'азабан-нар",
    "Раббигфирли ва ливалидаййа ва лиль-му'минина явма якумуль-хисаб",
    "Рабби-шрах ли садри ва яссир ли амри вахлюль-укдата мин лисани яфкаху каули",
    "Аллахумма инни ас'алюка 'ильман нафи'ан, ва ризкан тэййибан, ва 'амалян мутакаббалян",
    "Аллахумма инни а'узу бика мин 'азабиль-кабр, ва мин 'азаби джаханнам, ва мин фитнатиль-махйа валь-мамат",
    "Аллахумма инни а'узу бика мин аль-хамми валь-хазан, ва аль-аджзи валь-касал",
    "Астагфируллахаль-'азым аллязи ля иляха илля хуваль-хайюль-кайюму ва атубу иляйх",
    "Ля иляха илля анта субханака инни кунту миназ-залимин",
    "Хасбияллаху ля иляха илля хува 'аляйхи таваккальту ва хува раббуль-'аршиль-'азым",
]

# Файл для сохранения состояния
STATE_FILE = "dua_state.json"

# ==================== ЛОГИРОВАНИЕ ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../dua_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('DuaBot')

# ==================== КЛАСС ДЛЯ УПРАВЛЕНИЯ СОСТОЯНИЕМ ====================

class DuaStateManager:
    """Управление состоянием отправленных уведомлений"""
    
    def __init__(self, state_file=STATE_FILE):
        self.state_file = state_file
        self.state = self.load_state()
        logger.info(f"📂 Менеджер состояния инициализирован. Файл: {state_file}")
    
    def load_state(self):
        """Загружаем состояние из файла"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    logger.info(f"📥 Загружено состояние: {len(state)} записей")
                    return state
            else:
                logger.info("📭 Файл состояния не найден, создаем новый")
                return {}
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки состояния: {e}")
            return {}
    
    def save_state(self):
        """Сохраняем состояние в файл"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            logger.debug("💾 Состояние сохранено")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения состояния: {e}")
            return False
    
    def was_notification_sent_today(self, dua_name, current_date):
        """Проверяем, отправлялось ли уведомление сегодня"""
        key = f"{current_date}_{dua_name}"
        return key in self.state
    
    def mark_notification_sent(self, dua_name, current_date, current_time):
        """Отмечаем уведомление как отправленное"""
        key = f"{current_date}_{dua_name}"
        self.state[key] = {
            'sent_at': current_time,
            'timestamp': time.time(),
            'dua_name': dua_name
        }
        self.save_state()
        logger.info(f"📝 Уведомление '{dua_name}' отмечено как отправленное")
    
    def cleanup_old_entries(self):
        """Очищаем старые записи (старше 2 дней)"""
        current_time = time.time()
        two_days_ago = current_time - (2 * 24 * 60 * 60)  # 2 дня в секундах
        
        initial_count = len(self.state)
        keys_to_remove = []
        
        for key, entry in self.state.items():
            timestamp = entry.get('timestamp', 0)
            if timestamp < two_days_ago:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.state[key]
        
        if keys_to_remove:
            logger.info(f"🧹 Очищено {len(keys_to_remove)} старых записей")
            self.save_state()
        
        return len(keys_to_remove)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def check_bot_connection():
    """Проверяем, что бот доступен в Telegram"""
    logger.info("🔌 Проверяем подключение к Telegram API...")
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_name = data['result']['username']
                logger.info(f"✅ Бот @{bot_name} доступен")
                return True
            else:
                logger.error(f"❌ Ошибка в ответе API: {data}")
                return False
        else:
            logger.error(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("⏰ Таймаут при подключении к Telegram")
        return False
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return False

def get_random_dua():
    """Возвращает случайное дуа из базы"""
    return random.choice(DUA_DATABASE)

def get_current_time_utc5():
    """Возвращает текущее время в UTC+5 (Уфа)"""
    utc_plus_5 = timezone(timedelta(hours=5))
    now = datetime.now(utc_plus_5)
    return now.strftime("%H:%M"), now.strftime("%Y-%m-%d"), now

def create_dua_message(dua_time_info):
    """Создает сообщение с напоминанием о дуа"""
    dua = get_random_dua()
    
    message = f"""
{dua_time_info['emoji']} <b>ВРЕМЯ ДУА</b> {dua_time_info['emoji']}

🕐 <b>{dua_time_info['name']}</b>
⏰ Время: {dua_time_info['time']}

📿 <b>Дуа на сейчас:</b>

{dua}

✨ <i>"Поминайте Меня, и Я буду помнить о вас" (Коран 2:152)</i>

🤲 <b>Не откладывай! Сделай дуа сейчас!</b>

#дуа #зикр #напоминание
    """
    return message.strip()

def send_telegram_message(text):
    """Отправляет сообщение в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': 'HTML',
            'disable_notification': False
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Сообщение отправлено в Telegram")
            return True
        else:
            logger.error(f"❌ Ошибка Telegram API: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки в Telegram: {e}")
        return False

def is_time_for_dua(current_time_str, target_time_str, tolerance_minutes=2):
    """Проверяет, совпадает ли текущее время с целевым с допуском"""
    try:
        current = datetime.strptime(current_time_str, "%H:%M")
        target = datetime.strptime(target_time_str, "%H:%M")
        
        time_diff = abs((current - target).total_seconds() / 60)
        
        if time_diff <= tolerance_minutes:
            logger.debug(f"⏱️  Время совпало: {current_time_str} ~ {target_time_str} (разница: {time_diff:.1f} мин)")
            return True
        return False
    except ValueError as e:
        logger.error(f"❌ Ошибка парсинга времени: {e}")
        return False

def check_dua_times(state_manager):
    """Проверяет все времена для дуа и отправляет уведомления если нужно"""
    current_time, current_date, now = get_current_time_utc5()
    
    for dua_time in DUA_TIMES:
        dua_name = dua_time['name']
        dua_schedule_time = dua_time['time']
        
        if is_time_for_dua(current_time, dua_schedule_time):
            # Проверяем, не отправляли ли уже это уведомление сегодня
            if state_manager.was_notification_sent_today(dua_name, current_date):
                logger.info(f"⏭️  Уведомление '{dua_name}' уже отправлено сегодня")
                continue
            
            logger.info(f"🕋 Настало время для {dua_name}!")
            
            # Создаем и отправляем сообщение
            message = create_dua_message(dua_time)
            if send_telegram_message(message):
                # Сохраняем факт отправки
                state_manager.mark_notification_sent(dua_name, current_date, current_time)
                logger.info(f"✅ Напоминание о {dua_name} отправлено и сохранено")
                return True
            else:
                logger.error(f"❌ Не удалось отправить напоминание о {dua_name}")
                return False
    
    return False

def print_schedule_info():
    """Выводит информацию о расписании"""
    logger.info("📅 РАСПИСАНИЕ НАПОМИНАНИЙ О ДУА:")
    for dua_time in DUA_TIMES:
        logger.info(f"   {dua_time['emoji']} {dua_time['name']}: {dua_time['time']}")
    
    logger.info(f"📊 Всего дуа в базе: {len(DUA_DATABASE)}")
    logger.info(f"📍 Часовой пояс: UTC+5 (Уфа)")

def main():
    """Основная функция запуска"""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК МИКРОСЕРВИСА ДЛЯ НАПОМИНАНИЙ О ДУА")
    logger.info("=" * 60)
    
    current_time, current_date, now = get_current_time_utc5()
    logger.info(f"📝 ID чата: {TELEGRAM_CHAT_ID}")
    logger.info(f"⏰ Время запуска: {current_time} ({current_date})")
    
    # Инициализируем менеджер состояния
    state_manager = DuaStateManager()
    
    # Очищаем старые записи при запуске
    cleaned = state_manager.cleanup_old_entries()
    if cleaned > 0:
        logger.info(f"🧹 При запуске очищено {cleaned} старых записей")
    
    # Шаг 1: Проверяем подключение
    if not check_bot_connection():
        logger.error("❌ Не удалось подключиться к Telegram. Выход.")
        return
    
    # Шаг 2: Отправляем приветственное сообщение
    welcome_message = f"""🕌 <b>БОТ ДЛЯ НАПОМИНАНИЙ О ДУА</b>

✅ <i>Бот успешно запущен!</i>

📅 <b>Расписание на сегодня ({current_date}):</b>
🌅 Утреннее дуа: 07:00
☀️ Дневное дуа: 14:00  
🌙 Вечернее дуа: 20:00

⏰ <b>Текущее время:</b> {current_time}

🤖 <b>Функции бота:</b>
• Напоминает 3 раза в день
• Отправляет разные дуа каждый раз
• Защита от повторных уведомлений
• Автоочистка истории

🤲 <b>Да поможет нам Аллах поминать Его постоянно!</b>

#дуа #зикр #напоминание"""
    
    if not send_telegram_message(welcome_message):
        logger.error("⚠️ Не удалось отправить приветственное сообщение, но продолжаем...")
    
    # Шаг 3: Выводим информацию о расписании
    print_schedule_info()
    
    # Шаг 4: Основной рабочий цикл
    logger.info("\n🔁 ЗАПУСКАЕМ ОСНОВНОЙ ЦИКЛ ПРОВЕРКИ")
    logger.info("Бот будет проверять время каждые 30 секунд")
    logger.info("Для остановки нажмите Ctrl+C\n")
    
    try:
        check_counter = 0
        last_cleanup_time = time.time()
        
        while True:
            check_counter += 1
            current_time_str, current_date_str, _ = get_current_time_utc5()
            
            # Выводим статус каждые 30 проверок (15 минут)
            if check_counter % 30 == 0:
                logger.info(f"⏳ Бот активен. Время: {current_time_str}. Проверок: {check_counter}")
                logger.info(f"📊 Состояние: {len(state_manager.state)} сохраненных уведомлений")
            
            # Очищаем старые записи раз в 6 часов
            current_timestamp = time.time()
            if current_timestamp - last_cleanup_time > 6 * 3600:  # 6 часов
                cleaned = state_manager.cleanup_old_entries()
                if cleaned > 0:
                    logger.info(f"🧹 Периодическая очистка: удалено {cleaned} старых записей")
                last_cleanup_time = current_timestamp
            
            # Проверяем время для дуа
            notification_sent = check_dua_times(state_manager)
            
            # Если отправили уведомление, ждем дольше
            if notification_sent:
                logger.info("✅ Уведомление отправлено. Ждем 2 минуты...")
                time.sleep(120)  # 2 минуты
            else:
                time.sleep(30)  # 30 секунд
                
    except KeyboardInterrupt:
        logger.info("\n\n🛑 ОСТАНОВКА ПО ТРЕБОВАНИЮ ПОЛЬЗОВАТЕЛЯ")
        
        # Сохраняем состояние перед выходом
        state_manager.save_state()
        
        # Отправляем сообщение о завершении
        goodbye_message = "🕌 <b>Бот для напоминаний о дуа завершил работу</b>\n\nСостояние сохранено. До новых встреч, иншаАллах! 🤲"
        send_telegram_message(goodbye_message)
        
        logger.info("✅ Состояние сохранено")
        logger.info("🎉 Микросервис завершил работу корректно")
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА В ОСНОВНОМ ЦИКЛЕ: {e}")
        logger.error("🛑 Принудительная остановка микросервиса")
        
        # Пытаемся сохранить состояние даже при ошибке
        try:
            state_manager.save_state()
            logger.info("⚠️ Состояние сохранено перед аварийным выходом")
        except:
            logger.error("❌ Не удалось сохранить состояние")

if __name__ == "__main__":
    main()
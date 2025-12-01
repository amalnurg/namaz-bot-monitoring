# tests/test_scheduler.py
import pytest
import sys
import os
from unittest.mock import Mock, patch
from freezegun import freeze_time

# Добавляем родительскую папку в путь Python
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

class TestPrayerTimeChecker:
    
    @freeze_time("2024-01-15 07:25:00")  # 07:25 UTC = 12:25 UTC+5 (Уфа)
    def test_check_prayer_time_5_minutes_before(self):
        """Тест уведомления за 5 минут до намаза"""
        from namaz_bot import check_prayer_time
        
        timings = {
            'Fajr': '05:30',
            'Dhuhr': '12:30', 
            'Asr': '15:45',
            'Maghrib': '18:20',
            'Isha': '19:45'
        }
        
        sent_notifications = {}
        
        with patch('namaz_bot.send_telegram_message') as mock_send:
            mock_send.return_value = True
            
            notification_sent, updated_notifications = check_prayer_time(
                timings, sent_notifications
            )
        
        assert notification_sent is True
        assert 'Зухр_2024-01-15' in updated_notifications
        assert mock_send.called
    
    @freeze_time("2024-01-15 07:20:00")  # 07:20 UTC = 12:20 UTC+5 (Уфа)
    def test_check_prayer_time_10_minutes_before(self):
        """Тест что уведомление НЕ отправляется за 10 минут"""
        from namaz_bot import check_prayer_time
        
        timings = {
            'Fajr': '05:30',
            'Dhuhr': '12:30', 
            'Asr': '15:45',
            'Maghrib': '18:20',
            'Isha': '19:45'
        }
        
        sent_notifications = {}
        
        with patch('namaz_bot.send_telegram_message') as mock_send:
            notification_sent, updated_notifications = check_prayer_time(
                timings, sent_notifications
            )
        
        assert notification_sent is False
        assert len(updated_notifications) == 0
        mock_send.assert_not_called()
    
    @freeze_time("2024-01-15 07:25:00")  # 07:25 UTC = 12:25 UTC+5 (Уфа)
    def test_check_prayer_time_already_sent_today(self):
        """Тест что уведомление не отправляется повторно в тот же день"""
        from namaz_bot import check_prayer_time
        
        timings = {
            'Fajr': '05:30',
            'Dhuhr': '12:30', 
            'Asr': '15:45',
            'Maghrib': '18:20',
            'Isha': '19:45'
        }
        
        # Уже отправляли уведомление сегодня
        sent_notifications = {
            'Зухр_2024-01-15': {'sent_at': '12:25', 'timestamp': 1600000000}
        }
        
        with patch('namaz_bot.send_telegram_message') as mock_send:
            notification_sent, updated_notifications = check_prayer_time(
                timings, sent_notifications
            )
        
        assert notification_sent is False
        mock_send.assert_not_called()
    
    @freeze_time("2024-01-15 15:00:00")  # 15:00 UTC = 20:00 UTC+5 (Уфа) - после всех намазов
    def test_find_next_prayer_next_day(self):
        """Тест поиска ближайшего намаза на следующий день"""
        from namaz_bot import check_prayer_time
        
        timings = {
            'Fajr': '05:30',
            'Dhuhr': '12:30', 
            'Asr': '15:45',
            'Maghrib': '18:20',
            'Isha': '19:45'
        }
        
        sent_notifications = {}
        
        notification_sent, updated_notifications = check_prayer_time(
            timings, sent_notifications
        )
        
        # Должен найти Фаджр на следующий день (16 января)
        assert notification_sent is False
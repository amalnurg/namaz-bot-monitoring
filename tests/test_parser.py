# tests/test_parser.py
import pytest
import requests
import sys
import os
from unittest.mock import Mock, patch

# Добавляем родительскую папку в путь Python
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

class TestGetPrayerTimes:
    
    def test_successful_api_call(self, mock_api_response):
        """Тест успешного получения расписания от API"""
        # Мокаем requests.get чтобы не делать реальные запросы
        with patch('namaz_bot.requests.get') as mock_get:
            # Настраиваем mock чтобы возвращал успешный ответ
            mock_get.return_value = Mock(
                status_code=200,
                json=Mock(return_value=mock_api_response)
            )
            
            # Импортируем и тестируем нашу функцию
            from namaz_bot import get_prayer_times
            result = get_prayer_times()
            
            # Проверяем что функция вернула правильные данные
            assert result is not None
            assert result['Fajr'] == '05:30'
            assert result['Dhuhr'] == '12:30'
            assert result['Isha'] == '19:45'
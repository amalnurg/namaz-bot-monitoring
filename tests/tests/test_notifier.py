# tests/test_notifier.py
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Добавляем родительскую папку в путь Python
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

class TestTelegramNotifier:
    
    @patch('requests.post')
    def test_send_telegram_message_success(self, mock_post):
        """Тест успешной отправки сообщения в Telegram"""
        from namaz_bot import send_telegram_message
        
        # Настраиваем mock для успешного ответа
        mock_post.return_value = Mock(status_code=200)
        
        result = send_telegram_message("Тестовое сообщение")
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_telegram_message_failure(self, mock_post):
        """Тест неудачной отправки сообщения в Telegram"""
        from namaz_bot import send_telegram_message
        
        # Настраиваем mock для ошибки
        mock_post.return_value = Mock(status_code=400, text="Bad Request")
        
        result = send_telegram_message("Тестовое сообщение")
        
        assert result is False
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_telegram_message_exception(self, mock_post):
        """Тест исключения при отправке в Telegram"""
        from namaz_bot import send_telegram_message
        
        # Настраиваем mock для исключения
        mock_post.side_effect = Exception("Network error")
        
        result = send_telegram_message("Тестовое сообщение")
        
        assert result is False
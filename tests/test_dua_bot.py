import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dua_reminder.dua_bot import (
    DUA_DATABASE,
    get_random_dua,
    DUA_TIMES,
    is_time_for_dua,
    DuaStateManager
)


def test_basic_import():
    """Тест импорта модуля"""
    print("✅ Модуль dua_bot импортирован")
    assert len(DUA_DATABASE) > 0
    print(f"✅ В базе {len(DUA_DATABASE)} дуа")


def test_get_random_dua():
    """Тест получения случайного дуа"""
    dua = get_random_dua()
    assert isinstance(dua, str)
    assert len(dua) > 10
    print(f"✅ Получено дуа: {dua[:50]}...")


def test_time_config():
    """Тест конфигурации времени"""
    assert len(DUA_TIMES) == 3
    print("✅ Настроено 3 времени для напоминаний")
    
    for t in DUA_TIMES:
        print(f"   {t['emoji']} {t['name']}: {t['time']}")


def test_time_matching():
    """Тест сравнения времени"""
    # Точное совпадение
    assert is_time_for_dua("14:00", "14:00") == True
    # В пределах 2 минут
    assert is_time_for_dua("14:01", "14:00") == True
    assert is_time_for_dua("13:59", "14:00") == True
    # За пределами
    assert is_time_for_dua("14:03", "14:00") == False
    assert is_time_for_dua("13:57", "14:00") == False
    print("✅ Логика сравнения времени работает")


def test_state_manager():
    """Тест менеджера состояния"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        temp_file = f.name
    
    try:
        manager = DuaStateManager(state_file=temp_file)
        
        # Добавляем запись
        manager.mark_notification_sent("Утреннее дуа", "2025-12-02", "07:00")
        
        # Проверяем
        assert manager.was_notification_sent_today("Утреннее дуа", "2025-12-02") == True
        assert manager.was_notification_sent_today("Дневное дуа", "2025-12-02") == False
        assert manager.was_notification_sent_today("Утреннее дуа", "2025-12-03") == False
        
        print("✅ Менеджер состояния работает")
    finally:
        os.unlink(temp_file)


# Запуск всех тестов
if __name__ == "__main__":
    print("🧪 Запуск тестов для dua_bot...")
    
    tests = [
        test_basic_import,
        test_get_random_dua,
        test_time_config,
        test_time_matching,
        test_state_manager
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Тест {test_func.__name__} упал: {e}")
            raise
    
    print("\n🎉 Все 5 тестов пройдены!")
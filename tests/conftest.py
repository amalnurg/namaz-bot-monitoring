import pytest
from unittest.mock import Mock

@pytest.fixture
def sample_prayer_times():
    return {
        'Fajr': '05:30',
        'Dhuhr': '12:30', 
        'Asr': '15:45',
        'Maghrib': '18:20',
        'Isha': '19:45'
    }

@pytest.fixture
def mock_api_response(sample_prayer_times):
    return {
        'code': 200,
        'data': {'timings': sample_prayer_times}
    }
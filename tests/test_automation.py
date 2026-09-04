from autobiometrik.config import Config
from autobiometrik.automation import (
    is_autoit_available,
    start_frista_task,
    start_finger_task,
    stop_frista,
    stop_finger,
)


def test_automation_graceful_execution():
    config = Config()
    # These should execute cleanly without raising exceptions on any platform
    start_frista_task("0001234567890", config)
    start_finger_task("0001234567890", config)
    assert stop_frista() is True
    assert stop_finger() is True

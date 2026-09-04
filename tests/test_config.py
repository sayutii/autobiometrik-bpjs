import os
import json
import pytest
from autobiometrik.config import Config, DEFAULT_CONFIG


def test_default_config():
    cfg = Config()
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 5000
    assert cfg.has_credentials is False
    assert cfg.has_finger_credentials is False
    assert cfg.is_tls_enabled is False


def test_config_from_dict():
    cfg = Config({
        "frista_username": "user1",
        "frista_password": "pass1",
        "finger_username": "finger_user",
        "finger_password": "finger_pass",
        "tls_cert": "cert.pem",
        "tls_key": "key.pem",
        "port": 5050
    })
    assert cfg.frista_username == "user1"
    assert cfg.frista_password == "pass1"
    assert cfg.has_credentials is True
    assert cfg.has_finger_credentials is True
    assert cfg.is_tls_enabled is True
    assert cfg.port == 5050


def test_legacy_keys_compatibility():
    cfg = Config({
        "path": r"C:\custom\frista.exe",
        "pathfinger": r"C:\custom\after.exe"
    })
    assert cfg.frista_path == r"C:\custom\frista.exe"
    assert cfg.finger_path == r"C:\custom\after.exe"


def test_load_from_json_file(tmp_path):
    config_file = tmp_path / "config.json"
    data = {
        "frista_username": "admin",
        "frista_password": "secretpassword",
        "port": 6000
    }
    config_file.write_text(json.dumps(data), encoding="utf-8")

    cfg = Config.load(str(config_file))
    assert cfg.frista_username == "admin"
    assert cfg.frista_password == "secretpassword"
    assert cfg.port == 6000

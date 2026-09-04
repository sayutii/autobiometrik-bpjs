import os
import json
import configparser
from typing import Dict, Any, Optional

DEFAULT_CONFIG: Dict[str, Any] = {
    "frista_path": r"C:\frista\frista.exe",
    "finger_path": r"C:\Program Files (x86)\BPJS Kesehatan\Aplikasi Sidik Jari BPJS Kesehatan\After.exe",
    "frista_username": "",
    "frista_password": "",
    "finger_username": "",
    "finger_password": "",
    "host": "127.0.0.1",
    "port": 5000,
    "tls_cert": "",
    "tls_key": "",
    "frista_api": "https://frista.bpjs-kesehatan.go.id/frista-api",
    "camera_id": 0,
}


class Config:
    """
    Kelas penanganan konfigurasi AutoBiometrik BPJS.
    Mendukung pembacaan dari config.json, environment variable AUTOBIOMETRIK_CONFIG,
    dan kompatibilitas backward dengan format legacy config.conf / key lama (path, pathfinger).
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.data: Dict[str, Any] = dict(DEFAULT_CONFIG)
        if config_dict:
            self.data.update(config_dict)
            self._apply_legacy_keys(self.data)

    @staticmethod
    def _apply_legacy_keys(data: Dict[str, Any]) -> None:
        if "path" in data and ("frista_path" not in data or data["frista_path"] == DEFAULT_CONFIG["frista_path"]):
            data["frista_path"] = data["path"]
        if "pathfinger" in data and ("finger_path" not in data or data["finger_path"] == DEFAULT_CONFIG["finger_path"]):
            data["finger_path"] = data["pathfinger"]

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """
        Memuat konfigurasi dari file JSON atau INI (.conf).
        Jika config_path tidak ditentukan, akan memeriksa env AUTOBIOMETRIK_CONFIG,
        kemudian config.json, lalu fallback ke config.conf.
        """
        data = dict(DEFAULT_CONFIG)

        target_path = config_path or os.getenv("AUTOBIOMETRIK_CONFIG")

        if not target_path:
            if os.path.exists("config.json"):
                target_path = "config.json"
            elif os.path.exists("config.conf"):
                target_path = "config.conf"

        if target_path and os.path.exists(target_path):
            if target_path.endswith(".json"):
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        json_data = json.load(f)
                        data.update(json_data)
                except Exception as e:
                    print(f"[WARN] Gagal membaca {target_path}: {e}")
            elif target_path.endswith(".conf"):
                try:
                    parser = configparser.ConfigParser()
                    parser.read(target_path, encoding="utf-8")
                    if "Config" in parser:
                        sec = parser["Config"]
                        if "api" in sec:
                            data["frista_api"] = sec["api"]
                        if "camera_id" in sec:
                            try:
                                data["camera_id"] = int(sec["camera_id"])
                            except ValueError:
                                pass
                except Exception as e:
                    print(f"[WARN] Gagal membaca legacy config.conf: {e}")

        cls._apply_legacy_keys(data)

        return cls(data)

    @property
    def frista_path(self) -> str:
        return str(self.data.get("frista_path", DEFAULT_CONFIG["frista_path"]))

    @property
    def finger_path(self) -> str:
        return str(self.data.get("finger_path", DEFAULT_CONFIG["finger_path"]))

    @property
    def frista_username(self) -> str:
        return str(self.data.get("frista_username", ""))

    @property
    def frista_password(self) -> str:
        return str(self.data.get("frista_password", ""))

    @property
    def finger_username(self) -> str:
        return str(self.data.get("finger_username", ""))

    @property
    def finger_password(self) -> str:
        return str(self.data.get("finger_password", ""))

    @property
    def host(self) -> str:
        return str(self.data.get("host", DEFAULT_CONFIG["host"]))

    @property
    def port(self) -> int:
        try:
            return int(self.data.get("port", DEFAULT_CONFIG["port"]))
        except ValueError:
            return 5000

    @property
    def tls_cert(self) -> str:
        return str(self.data.get("tls_cert", ""))

    @property
    def tls_key(self) -> str:
        return str(self.data.get("tls_key", ""))

    @property
    def frista_api(self) -> str:
        return str(self.data.get("frista_api", DEFAULT_CONFIG["frista_api"]))

    @property
    def camera_id(self) -> int:
        try:
            return int(self.data.get("camera_id", DEFAULT_CONFIG["camera_id"]))
        except ValueError:
            return 0

    @property
    def has_credentials(self) -> bool:
        """Memeriksa apakah kredensial FRISTA diisi."""
        return bool(self.frista_username and self.frista_password)

    @property
    def has_finger_credentials(self) -> bool:
        """Memeriksa apakah kredensial aplikasi sidik jari diisi."""
        return bool(self.finger_username and self.finger_password)

    @property
    def is_tls_enabled(self) -> bool:
        """Memeriksa apakah TLS / HTTPS diaktifkan melalui tls_cert dan tls_key."""
        return bool(self.tls_cert and self.tls_key)

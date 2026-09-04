"""
File titik masuk (entrypoint) saat dijalankan melalui `python -m autobiometrik` atau `.exe`.
"""

import sys
import os
import traceback
import logging


def get_app_dir() -> str:
    """Mengembalikan direktori lokasi executable atau script berjalan."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


LOG_FILE = os.path.join(get_app_dir(), "autobiometrik.log")


class LoggerTee:
    """Mengarahkan sys.stdout dan sys.stderr ke terminal dan file log secara bersamaan."""

    def __init__(self, original_stream, log_file_path):
        self.original_stream = original_stream
        self.log_file_path = log_file_path

    def write(self, message):
        try:
            self.original_stream.write(message)
            self.original_stream.flush()
        except Exception:
            pass

        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(message)
        except Exception:
            pass

    def flush(self):
        try:
            self.original_stream.flush()
        except Exception:
            pass


# Redirect stdout and stderr ke file log
sys.stdout = LoggerTee(sys.stdout, LOG_FILE)
sys.stderr = LoggerTee(sys.stderr, LOG_FILE)


def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    print("\n" + "!" * 60)
    print(f" [CRITICAL ERROR] Service gagal berjalan!")
    print(f" Detail error telah dicatat ke: {LOG_FILE}")
    print("!" * 60)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    print("!" * 60)
    try:
        input("\nTekan ENTER untuk menutup jendela ini...")
    except Exception:
        pass
    sys.exit(1)


sys.excepthook = global_exception_handler

# Top-level imports after exception handler setup
from .config import Config
from .server import run_server


def main() -> None:
    print("=" * 60)
    print(" AutoBiometrik BPJS - Local HTTP Bridge Service")
    print(f" Log File: {LOG_FILE}")
    print("=" * 60)
    try:
        config = Config.load()
        print(f"FRISTA Path   : {config.frista_path}")
        print(f"Finger Path   : {config.finger_path}")
        print(f"Host & Port   : {config.host}:{config.port}")
        print(f"Credentials   : FRISTA={config.has_credentials}, Finger={config.has_finger_credentials}")
        print("=" * 60)

        run_server(config)
    except KeyboardInterrupt:
        print("\n[INFO] Service dihentikan oleh pengguna.")
        sys.exit(0)
    except Exception as e:
        global_exception_handler(type(e), e, e.__traceback__)


if __name__ == "__main__":
    main()

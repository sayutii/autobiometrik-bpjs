import sys
import time
import subprocess
from typing import Optional
from .config import Config

AUTOIT_AVAILABLE = False
AUTOIT_ERROR = ""

try:
    if sys.platform == "win32":
        import autoit  # type: ignore
        AUTOIT_AVAILABLE = True
except Exception as e:
    AUTOIT_AVAILABLE = False
    AUTOIT_ERROR = str(e)
    print(f"[WARN] PyAutoIt import exception: {e}")
except BaseException as e:
    AUTOIT_AVAILABLE = False
    AUTOIT_ERROR = str(e)
    print(f"[WARN] PyAutoIt base exception: {e}")

# Window Titles & Identifiers for AutoIt
FRISTA_TITLE = "FRISTA"
FRISTA_PROCESS = "frista.exe"

FINGER_TITLE = "Aplikasi Sidik Jari BPJS Kesehatan"
FINGER_TITLE_ALT = "After"
FINGER_PROCESS = "After.exe"


def is_autoit_available() -> bool:
    """Mengembalikan status ketersediaan AutoItX di sistem."""
    return AUTOIT_AVAILABLE


def _focus_or_launch(exe_path: str, win_title: str) -> bool:
    """
    Mengecek apakah jendela aplikasi sudah ada.
    Jika ada: mengaktifkan jendela tersebut (focus).
    Jika belum: menjalankan file executable aplikasi.
    """
    if not AUTOIT_AVAILABLE:
        print(f"[MOCK] Focusing/Launching {exe_path}")
        return True

    try:
        if autoit.win_exists(win_title):
            autoit.win_activate(win_title)
            autoit.win_wait_active(win_title, 3)
            return True
        else:
            subprocess.Popen([exe_path])
            return False
    except Exception as e:
        print(f"[ERROR] Gagal membuka/memfokuskan {exe_path}: {e}")
        return False


def start_frista_task(no_peserta: str, config: Config) -> None:
    """
    Tugas otomatisasi background untuk aplikasi FRISTA.
    - Jika belum jalan: buka, login otomatis dengan frista_username & frista_password.
    - Ketikkan no_peserta ke kolom 'No. BPJS Kesehatan/NIK'.
    """
    if not AUTOIT_AVAILABLE:
        print(f"[MOCK] FRISTA automation executed for no_peserta: {no_peserta}")
        return

    already_running = _focus_or_launch(config.frista_path, FRISTA_TITLE)

    try:
        if not already_running:
            # Tunggu hingga jendela FRISTA muncul
            autoit.win_wait(FRISTA_TITLE, timeout=10)
            autoit.win_activate(FRISTA_TITLE)
            autoit.win_wait_active(FRISTA_TITLE, timeout=5)

            # Jika ada kredensial FRISTA, lakukan login otomatis
            if config.has_credentials:
                time.sleep(1)
                # Mengisi Username dan Password
                autoit.send("^a{DEL}")  # Select all & delete
                autoit.send(config.frista_username)
                autoit.send("{TAB}")
                autoit.send(config.frista_password)
                autoit.send("{ENTER}")
                time.sleep(2)

        # Setelah di layar utama / aktif, ketikkan nomor BPJS
        autoit.win_activate(FRISTA_TITLE)
        autoit.win_wait_active(FRISTA_TITLE, timeout=5)
        time.sleep(0.5)

        # Fokuskan dan ketikkan nomor peserta
        autoit.send("^a{DEL}")
        autoit.send(no_peserta)
        print(f"[SUCCESS] FRISTA dikirim no_peserta: {no_peserta}")

    except Exception as e:
        print(f"[ERROR] Otorisasi/Input FRISTA gagal: {e}")


def start_finger_task(no_peserta: str, config: Config) -> None:
    """
    Tugas otomatisasi background untuk aplikasi Sidik Jari (After.exe).
    - Jika belum jalan: buka, login otomatis (jika finger_username tersedia).
    - Ketikkan no_peserta ke kolom input nomor BPJS.
    """
    if not AUTOIT_AVAILABLE:
        print(f"[MOCK] Fingerprint automation executed for no_peserta: {no_peserta}")
        return

    already_running = autoit.win_exists(FINGER_TITLE) or autoit.win_exists(FINGER_TITLE_ALT)
    target_title = FINGER_TITLE if autoit.win_exists(FINGER_TITLE) else FINGER_TITLE_ALT

    if already_running:
        autoit.win_activate(target_title)
        autoit.win_wait_active(target_title, 3)
    else:
        subprocess.Popen([config.finger_path])
        target_title = FINGER_TITLE
        autoit.win_wait(target_title, timeout=10)
        autoit.win_activate(target_title)
        autoit.win_wait_active(target_title, timeout=5)

        # Login jika finger_username diisi
        if config.has_finger_credentials:
            time.sleep(1)
            autoit.send("^a{DEL}")
            autoit.send(config.finger_username)
            autoit.send("{TAB}")
            autoit.send(config.finger_password)
            autoit.send("{ENTER}")
            time.sleep(2)

    try:
        autoit.win_activate(target_title)
        autoit.win_wait_active(target_title, timeout=5)
        time.sleep(0.5)

        autoit.send("^a{DEL}")
        autoit.send(no_peserta)
        print(f"[SUCCESS] Fingerprint dikirim no_peserta: {no_peserta}")
    except Exception as e:
        print(f"[ERROR] Input Aplikasi Sidik Jari gagal: {e}")


def stop_frista() -> bool:
    """Menutup aplikasi FRISTA jika sedang berjalan."""
    if not AUTOIT_AVAILABLE:
        print("[MOCK] FRISTA stopped")
        return True

    try:
        if autoit.win_exists(FRISTA_TITLE):
            autoit.win_close(FRISTA_TITLE)
        autoit.process_close(FRISTA_PROCESS)
        return True
    except Exception as e:
        print(f"[WARN] Stop FRISTA failed: {e}")
        return False


def stop_finger() -> bool:
    """Menutup aplikasi Sidik Jari (After.exe) jika sedang berjalan."""
    if not AUTOIT_AVAILABLE:
        print("[MOCK] Aplikasi Sidik Jari stopped")
        return True

    try:
        if autoit.win_exists(FINGER_TITLE):
            autoit.win_close(FINGER_TITLE)
        if autoit.win_exists(FINGER_TITLE_ALT):
            autoit.win_close(FINGER_TITLE_ALT)
        autoit.process_close(FINGER_PROCESS)
        return True
    except Exception as e:
        print(f"[WARN] Stop Sidik Jari failed: {e}")
        return False

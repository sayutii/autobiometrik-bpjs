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

# Process names for process_exists and process_close
FRISTA_PROCESS = "frista.exe"
FINGER_PROCESS = "After.exe"


def is_autoit_available() -> bool:
    """Mengembalikan status ketersediaan AutoItX di sistem."""
    return AUTOIT_AVAILABLE


def is_process_running(process_name: str) -> bool:
    """Mengecek apakah proses Windows sedang berjalan berdasarkan nama file .exe."""
    if not AUTOIT_AVAILABLE:
        return False
    try:
        res = autoit.process_exists(process_name)
        return bool(res and int(res) > 0)
    except Exception as e:
        print(f"[WARN] Error checking process {process_name}: {e}")
        return False


def _configure_autoit() -> None:
    """Mengatur mode pencarian jendela dan penundaan pengetikan di AutoIt."""
    if not AUTOIT_AVAILABLE:
        return
    try:
        autoit.opt("WinTitleMatchMode", 2)  # Match any substring in title
        autoit.opt("SendKeyDelay", 30)       # 30ms delay between keystrokes for GUI stability
    except Exception as e:
        print(f"[WARN] Gagal mengatur opsi AutoIt: {e}")


def start_frista_task(no_peserta: str, config: Config) -> None:
    """
    Tugas otomatisasi background untuk aplikasi FRISTA.
    - Jika belum jalan: buka, login otomatis dengan frista_username & frista_password.
    - Ketikkan no_peserta ke kolom 'No. BPJS Kesehatan/NIK'.
    """
    if not AUTOIT_AVAILABLE:
        print(f"[MOCK] FRISTA automation executed for no_peserta: {no_peserta}")
        return

    _configure_autoit()
    # Match window titles starting with FRISTA (e.g. FRISTA, FRISTA 3.0.1, Login FRISTA)
    # ^FRISTA prevents matching folder paths like C:\...\frista.v.3.0.1 in CMD or Explorer
    frista_win = "[REGEXPTITLE:(?i)^(FRISTA|Login FRISTA|Verifikasi Wajah)]"

    print(f"[INFO] Running start_frista_task for no_peserta: {no_peserta}")
    print(f"[INFO] FRISTA Config -> Path: '{config.frista_path}', User: '{config.frista_username}'")

    # Gunakan pengecekan nama proses executable frista.exe (bebas salah deteksi folder/browser)
    already_running = is_process_running(FRISTA_PROCESS)
    print(f"[INFO] FRISTA process ({FRISTA_PROCESS}) running: {already_running}")

    if not already_running:
        print(f"[INFO] Launching FRISTA process: {config.frista_path}")
        try:
            subprocess.Popen([config.frista_path])
        except Exception as err:
            print(f"[ERROR] Gagal membuka file executable FRISTA ({config.frista_path}): {err}")
            return

        time.sleep(2.5)  # Beri waktu proses GUI FRISTA inisialisasi awal

        # Tunggu hingga jendela FRISTA / Login muncul (maksimum 15 detik)
        wait_success = autoit.win_wait(frista_win, timeout=15)
        if not wait_success:
            print(f"[WARN] Timeout 15 detik menunggu jendela FRISTA ({frista_win}) muncul!")
        
        try:
            autoit.win_activate(frista_win)
            autoit.win_wait_active(frista_win, timeout=5)
        except Exception as err:
            print(f"[WARN] Gagal mengaktifkan jendela FRISTA: {err}")

        time.sleep(1.5)  # Tunggu sebentar hingga komponen GUI selesai dirender

        # Jika username FRISTA diisi di config.json, lakukan login otomatis
        if config.frista_username:
            print(f"[INFO] Mengisi kredensial FRISTA untuk user: '{config.frista_username}'")
            try:
                autoit.win_activate(frista_win)
                time.sleep(0.5)
                autoit.send("^a{DEL}")  # Select all & delete
                autoit.send(config.frista_username)
                autoit.send("{TAB}")
                time.sleep(0.3)
                autoit.send("^a{DEL}")
                autoit.send(config.frista_password)
                autoit.send("{ENTER}")
                print("[INFO] Form login FRISTA telah disubmit ({ENTER})")
                time.sleep(3.0)  # Tunggu proses login selesai dan masuk ke layar utama
            except Exception as err:
                print(f"[ERROR] Gagal mengisi kredensial FRISTA: {err}")
        else:
            print("[INFO] frista_username kosong di config.json, melewati langkah login.")

    # Setelah di layar utama / aktif, ketikkan nomor BPJS
    try:
        autoit.win_activate(frista_win)
        autoit.win_wait_active(frista_win, timeout=5)
        time.sleep(0.5)

        autoit.send("^a{DEL}")
        autoit.send(no_peserta)
        print(f"[SUCCESS] FRISTA berhasil dikirim no_peserta: {no_peserta}")
    except Exception as e:
        print(f"[ERROR] Input no_peserta ke FRISTA gagal: {e}")


def start_finger_task(no_peserta: str, config: Config) -> None:
    """
    Tugas otomatisasi background untuk aplikasi Sidik Jari (After.exe).
    - Jika belum jalan: buka, login otomatis (jika finger_username tersedia).
    - Ketikkan no_peserta ke kolom input nomor BPJS.
    """
    if not AUTOIT_AVAILABLE:
        print(f"[MOCK] Fingerprint automation executed for no_peserta: {no_peserta}")
        return

    _configure_autoit()
    # Matches titles starting with Aplikasi Sidik Jari, After, or Sidik Jari
    finger_win = "[REGEXPTITLE:(?i)^(Aplikasi Sidik Jari|After|Sidik Jari)]"

    print(f"[INFO] Running start_finger_task for no_peserta: {no_peserta}")
    print(f"[INFO] Finger Config -> Path: '{config.finger_path}', User: '{config.finger_username}'")

    # Gunakan pengecekan nama proses executable After.exe
    already_running = is_process_running(FINGER_PROCESS)
    print(f"[INFO] Finger process ({FINGER_PROCESS}) running: {already_running}")

    if not already_running:
        print(f"[INFO] Launching Finger process: {config.finger_path}")
        try:
            subprocess.Popen([config.finger_path])
        except Exception as err:
            print(f"[ERROR] Gagal membuka file executable Sidik Jari ({config.finger_path}): {err}")
            return

        time.sleep(2.5)  # Beri waktu proses GUI Sidik Jari inisialisasi awal

        wait_success = autoit.win_wait(finger_win, timeout=15)
        if not wait_success:
            print(f"[WARN] Timeout 15 detik menunggu jendela Sidik Jari ({finger_win}) muncul!")

        try:
            autoit.win_activate(finger_win)
            autoit.win_wait_active(finger_win, timeout=5)
        except Exception as err:
            print(f"[WARN] Gagal mengaktifkan jendela Sidik Jari: {err}")

        time.sleep(1.5)

        # Login jika finger_username diisi di config.json
        if config.finger_username:
            print(f"[INFO] Mengisi kredensial Sidik Jari untuk user: '{config.finger_username}'")
            try:
                autoit.win_activate(finger_win)
                time.sleep(0.5)
                autoit.send("^a{DEL}")
                autoit.send(config.finger_username)
                autoit.send("{TAB}")
                time.sleep(0.3)
                autoit.send("^a{DEL}")
                autoit.send(config.finger_password)
                autoit.send("{ENTER}")
                print("[INFO] Form login Sidik Jari telah disubmit ({ENTER})")
                time.sleep(3.0)
            except Exception as err:
                print(f"[ERROR] Gagal mengisi kredensial Sidik Jari: {err}")
        else:
            print("[INFO] finger_username kosong di config.json, melewati langkah login.")

    try:
        autoit.win_activate(finger_win)
        autoit.win_wait_active(finger_win, timeout=5)
        time.sleep(0.5)

        autoit.send("^a{DEL}")
        autoit.send(no_peserta)
        print(f"[SUCCESS] Aplikasi Sidik Jari berhasil dikirim no_peserta: {no_peserta}")
    except Exception as e:
        print(f"[ERROR] Input no_peserta ke Aplikasi Sidik Jari gagal: {e}")


def stop_frista() -> bool:
    """Menutup aplikasi FRISTA jika sedang berjalan."""
    if not AUTOIT_AVAILABLE:
        print("[MOCK] FRISTA stopped")
        return True

    _configure_autoit()
    frista_win = "[REGEXPTITLE:(?i)^(FRISTA|Login FRISTA|Verifikasi Wajah)]"

    try:
        if autoit.win_exists(frista_win):
            autoit.win_close(frista_win)
        autoit.process_close(FRISTA_PROCESS)
        print("[INFO] FRISTA berhasil dihentikan.")
        return True
    except Exception as e:
        print(f"[WARN] Stop FRISTA gagal: {e}")
        return False


def stop_finger() -> bool:
    """Menutup aplikasi Sidik Jari (After.exe) melepaskan proses After.exe."""
    if not AUTOIT_AVAILABLE:
        print("[MOCK] Aplikasi Sidik Jari stopped")
        return True

    _configure_autoit()
    finger_win = "[REGEXPTITLE:(?i)^(Aplikasi Sidik Jari|After|Sidik Jari)]"

    try:
        if autoit.win_exists(finger_win):
            autoit.win_close(finger_win)
        autoit.process_close(FINGER_PROCESS)
        print("[INFO] Aplikasi Sidik Jari berhasil dihentikan.")
        return True
    except Exception as e:
        print(f"[WARN] Stop Aplikasi Sidik Jari gagal: {e}")
        return False

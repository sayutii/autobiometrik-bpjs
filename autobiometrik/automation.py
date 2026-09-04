import sys
import time
import subprocess
from typing import Optional, List
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

# Process names for Windows process detection
FRISTA_PROCESS = "frista.exe"
FINGER_PROCESS = "After.exe"

# Window title patterns for FRISTA and Fingerprint app
FRISTA_PATTERNS = [
    "[CLASS:SunAwtFrame]",
    "FRISTA",
    "Login FRISTA",
    "Verifikasi Wajah",
    "[REGEXPTITLE:(?i)^FRISTA]",
    "[REGEXPTITLE:(?i).*(FRISTA).*]",
]

FINGER_PATTERNS = [
    "Aplikasi Sidik Jari BPJS Kesehatan",
    "Aplikasi Sidik Jari",
    "After",
    "Form Login",
    "BPJS Kesehatan",
    "[REGEXPTITLE:(?i)^(Aplikasi Sidik Jari|After|Sidik Jari)]",
    "[REGEXPTITLE:(?i).*(Sidik Jari|After).*]",
]


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
        autoit.opt("WinTitleMatchMode", 2)  # Substring matching
        autoit.opt("SendKeyDelay", 30)       # 30ms keystroke delay for GUI input stability
    except Exception as e:
        print(f"[WARN] Gagal mengatur opsi AutoIt: {e}")


def _send_keys(text: str, is_raw: bool = True) -> None:
    """
    Mengirimkan teks atau tombol ke jendela aktif menggunakan AutoIt.
    - is_raw=True: Mengirim teks mentah (raw), aman untuk password bersimbol seperti #, !, ^, +.
    - is_raw=False: Mengirim tombol kontrol seperti {TAB}, {ENTER}, ^a{DEL}.
    """
    if not AUTOIT_AVAILABLE:
        return
    raw_flag = 1 if is_raw else 0
    try:
        autoit.send(text, raw_flag)
    except TypeError:
        # Fallback jika autoit.send tidak mendukung argumen posisi kedua di versi tertentu
        try:
            if is_raw:
                autoit.send(f"{{RAW}}{text}")
            else:
                autoit.send(text)
        except Exception as e:
            print(f"[WARN] Error sending keys ({text}): {e}")
    except Exception as e:
        print(f"[WARN] Error sending keys ({text}): {e}")


def _wait_and_activate(patterns: List[str], timeout: float = 12.0) -> Optional[str]:
    """
    Mencoba menemukan dan mengaktifkan salah satu pola jendela dari daftar.
    Aman (tidak melempar AutoItError exception jika timeout).
    """
    if not AUTOIT_AVAILABLE:
        return None

    _configure_autoit()
    start_time = time.time()
    while time.time() - start_time < timeout:
        for pattern in patterns:
            try:
                if autoit.win_exists(pattern):
                    try:
                        autoit.win_activate(pattern)
                        autoit.win_wait_active(pattern, timeout=2)
                    except Exception:
                        pass
                    return pattern
            except Exception:
                pass
        time.sleep(0.5)

    print(f"[WARN] Tidak dapat mengaktifkan jendela dari daftar pola: {patterns}")
    return None


def _is_login_screen_active() -> bool:
    """Mengecek apakah jendela yang sedang aktif merupakan layar Login/Masuk."""
    if not AUTOIT_AVAILABLE:
        return False
    try:
        title = autoit.win_get_title("[ACTIVE]")
        if any(w in title.lower() for w in ["login", "masuk", "sign in", "authentication", "kredensial"]):
            return True
    except Exception:
        pass
    return False


def start_frista_task(no_peserta: str, config: Config) -> None:
    """
    Tugas otomatisasi background untuk aplikasi FRISTA.
    - Jika belum jalan / di layar login: buka & login otomatis (RAW mode untuk password bersimbol).
    - Ketikkan no_peserta ke kolom 'No. BPJS Kesehatan/NIK'.
    """
    if not AUTOIT_AVAILABLE:
        print(f"[MOCK] FRISTA automation executed for no_peserta: {no_peserta}")
        return

    _configure_autoit()

    print(f"[INFO] Running start_frista_task for no_peserta: {no_peserta}")
    print(f"[INFO] FRISTA Config -> Path: '{config.frista_path}', User: '{config.frista_username}'")

    already_running = is_process_running(FRISTA_PROCESS)
    print(f"[INFO] FRISTA process ({FRISTA_PROCESS}) running: {already_running}")

    login_needed = False

    if not already_running:
        print(f"[INFO] Launching FRISTA process: {config.frista_path}")
        try:
            subprocess.Popen([config.frista_path])
        except Exception as err:
            print(f"[ERROR] Gagal membuka file executable FRISTA ({config.frista_path}): {err}")
            return

        time.sleep(2.5)
        active_pat = _wait_and_activate(FRISTA_PATTERNS, timeout=15.0)
        print(f"[INFO] FRISTA active window pattern: {active_pat}")
        time.sleep(1.5)
        login_needed = True
    else:
        active_pat = _wait_and_activate(FRISTA_PATTERNS, timeout=5.0)
        if _is_login_screen_active():
            print("[INFO] FRISTA berjalan tapi terdeteksi masih di layar Login. Melakukan login otomatis...")
            login_needed = True

    # Proses Login Otomatis jika aplikasi baru dibuka atau masih di layar login
    if login_needed and config.frista_username:
        print(f"[INFO] Mengisi kredensial FRISTA (RAW mode) untuk user: '{config.frista_username}'")
        try:
            if active_pat:
                autoit.win_activate(active_pat)
            time.sleep(0.5)

            # Isi Username (is_raw=True)
            _send_keys("^a{DEL}", is_raw=False)
            _send_keys(config.frista_username, is_raw=True)
            time.sleep(0.3)

            # Pindah ke kolom Password
            _send_keys("{TAB}", is_raw=False)
            time.sleep(0.3)

            # Isi Password (is_raw=True aman untuk simbol #, !, ^, +)
            _send_keys("^a{DEL}", is_raw=False)
            _send_keys(config.frista_password, is_raw=True)
            time.sleep(0.3)

            # Submit Form Login dengan ENTER
            _send_keys("{ENTER}", is_raw=False)
            print("[INFO] Form login FRISTA disubmit dengan {ENTER}")
            time.sleep(0.5)

            # Fallback: tekan TAB lalu ENTER untuk memastikan tombol Login tertekan
            _send_keys("{TAB}", is_raw=False)
            _send_keys("{ENTER}", is_raw=False)
            print("[INFO] Fallback tombol Login FRISTA dikirim ({TAB} + {ENTER})")

            time.sleep(3.5)  # Tunggu login sukses dan masuk ke layar utama FRISTA
        except Exception as err:
            print(f"[ERROR] Gagal melakukan login FRISTA: {err}")
    elif not config.frista_username:
        print("[INFO] frista_username kosong di config.json, melewati langkah login.")

    # Ketikkan no_peserta
    try:
        active_pat = _wait_and_activate(FRISTA_PATTERNS, timeout=5.0)
        if active_pat:
            autoit.win_activate(active_pat)
        time.sleep(0.5)

        _send_keys("^a{DEL}", is_raw=False)
        _send_keys(no_peserta, is_raw=True)
        print(f"[SUCCESS] FRISTA berhasil dikirim no_peserta: {no_peserta}")
    except Exception as e:
        print(f"[ERROR] Input no_peserta ke FRISTA gagal: {e}")


def start_finger_task(no_peserta: str, config: Config) -> None:
    """
    Tugas otomatisasi background untuk aplikasi Sidik Jari (After.exe).
    - Jika belum jalan / di layar login: buka & login otomatis (RAW mode untuk password bersimbol).
    - Ketikkan no_peserta ke kolom input nomor BPJS.
    """
    if not AUTOIT_AVAILABLE:
        print(f"[MOCK] Fingerprint automation executed for no_peserta: {no_peserta}")
        return

    _configure_autoit()

    print(f"[INFO] Running start_finger_task for no_peserta: {no_peserta}")
    print(f"[INFO] Finger Config -> Path: '{config.finger_path}', User: '{config.finger_username}'")

    already_running = is_process_running(FINGER_PROCESS)
    print(f"[INFO] Finger process ({FINGER_PROCESS}) running: {already_running}")

    login_needed = False

    if not already_running:
        print(f"[INFO] Launching Finger process: {config.finger_path}")
        try:
            subprocess.Popen([config.finger_path])
        except Exception as err:
            print(f"[ERROR] Gagal membuka file executable Sidik Jari ({config.finger_path}): {err}")
            return

        time.sleep(2.5)
        active_pat = _wait_and_activate(FINGER_PATTERNS, timeout=15.0)
        print(f"[INFO] Finger active window pattern: {active_pat}")
        time.sleep(1.5)
        login_needed = True
    else:
        active_pat = _wait_and_activate(FINGER_PATTERNS, timeout=5.0)
        if _is_login_screen_active():
            print("[INFO] Sidik Jari berjalan tapi terdeteksi masih di layar Login. Melakukan login otomatis...")
            login_needed = True

    # Proses Login Otomatis jika aplikasi baru dibuka atau masih di layar login
    if login_needed and config.finger_username:
        print(f"[INFO] Mengisi kredensial Sidik Jari (RAW mode) untuk user: '{config.finger_username}'")
        try:
            if active_pat:
                autoit.win_activate(active_pat)
            time.sleep(0.5)

            # Isi Username
            _send_keys("^a{DEL}", is_raw=False)
            _send_keys(config.finger_username, is_raw=True)
            time.sleep(0.3)

            # Pindah ke kolom Password
            _send_keys("{TAB}", is_raw=False)
            time.sleep(0.3)

            # Isi Password (is_raw=True aman untuk simbol #, !, ^, +)
            _send_keys("^a{DEL}", is_raw=False)
            _send_keys(config.finger_password, is_raw=True)
            time.sleep(0.3)

            # Submit Form Login dengan ENTER
            _send_keys("{ENTER}", is_raw=False)
            print("[INFO] Form login Sidik Jari disubmit dengan {ENTER}")
            time.sleep(0.5)

            # Fallback: tekan TAB lalu ENTER untuk memastikan tombol Login tertekan
            _send_keys("{TAB}", is_raw=False)
            _send_keys("{ENTER}", is_raw=False)
            print("[INFO] Fallback tombol Login Sidik Jari dikirim ({TAB} + {ENTER})")

            time.sleep(3.5)  # Tunggu login sukses dan masuk ke layar utama Sidik Jari
        except Exception as err:
            print(f"[ERROR] Gagal melakukan login Sidik Jari: {err}")
    elif not config.finger_username:
        print("[INFO] finger_username kosong di config.json, melewati langkah login.")

    # Ketikkan no_peserta
    try:
        active_pat = _wait_and_activate(FINGER_PATTERNS, timeout=5.0)
        if active_pat:
            autoit.win_activate(active_pat)
        time.sleep(0.5)

        _send_keys("^a{DEL}", is_raw=False)
        _send_keys(no_peserta, is_raw=True)
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

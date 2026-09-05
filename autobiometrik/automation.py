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

# Exact Window Titles for FRISTA Login and Main windows
FRISTA_LOGIN_TITLES = [
    "Login Frista (Face Recognition BPJS Kesehatan)",
    "Login Frista",
    "Login FRISTA",
    "[TITLE:Login Frista (Face Recognition BPJS Kesehatan)]",
    "[TITLE:Login Frista]",
]

FRISTA_MAIN_TITLES = [
    "FRISTA (Face Recognition BPJS Kesehatan)",
    "FRISTA",
    "[CLASS:SunAwtFrame]",
    "[TITLE:FRISTA]",
]

# Exact Window Titles for Fingerprint app (After.exe)
FINGER_LOGIN_TITLES = [
    "Aplikasi Sidik Jari BPJS Kesehatan",
    "Form Login",
    "Login Aplikasi Sidik Jari",
    "Login",
    "[TITLE:Aplikasi Sidik Jari BPJS Kesehatan]",
    "[TITLE:Form Login]",
]

FINGER_MAIN_TITLES = [
    "Aplikasi Sidik Jari BPJS Kesehatan",
    "After",
    "[TITLE:After]",
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
        # Fallback jika autoit.send tidak mendukung argumen posisi kedua
        try:
            if is_raw:
                autoit.send(f"{{RAW}}{text}")
            else:
                autoit.send(text)
        except Exception as e:
            print(f"[WARN] Error sending keys ({text}): {e}")
    except Exception as e:
        print(f"[WARN] Error sending keys ({text}): {e}")


def _wait_and_activate(patterns: List[str], timeout: float = 10.0) -> Optional[str]:
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

    return None


def start_frista_task(no_peserta: str, config: Config) -> None:
    """
    Tugas otomatisasi background untuk aplikasi FRISTA.
    - Jika belum jalan / di layar login: buka & login otomatis.
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

    if not already_running:
        print(f"[INFO] Launching FRISTA process: {config.frista_path}")
        try:
            subprocess.Popen([config.frista_path])
        except Exception as err:
            print(f"[ERROR] Gagal membuka file executable FRISTA ({config.frista_path}): {err}")
            return

    # Cek apakah Jendela Login FRISTA ("Login Frista (Face Recognition BPJS Kesehatan)") ada
    login_win = _wait_and_activate(FRISTA_LOGIN_TITLES, timeout=12.0)
    print(f"[INFO] FRISTA login window detected: '{login_win}'")

    if login_win:
        # Kita berada di Layar Login FRISTA!
        if config.frista_username:
            print(f"[INFO] Mengisi kredensial FRISTA di '{login_win}' untuk user: '{config.frista_username}'")
            try:
                autoit.win_activate(login_win)
                autoit.win_wait_active(login_win, timeout=5)
                time.sleep(0.8)

                # Coba beri fokus ke area control username
                try:
                    autoit.control_focus(login_win, "")
                except Exception:
                    pass

                # Clear & Isi Username
                _send_keys("^a{DEL}", is_raw=False)
                _send_keys(config.frista_username, is_raw=True)
                time.sleep(0.3)

                # Pindah ke kolom Password
                _send_keys("{TAB}", is_raw=False)
                time.sleep(0.3)

                # Clear & Isi Password
                _send_keys("^a{DEL}", is_raw=False)
                _send_keys(config.frista_password, is_raw=True)
                time.sleep(0.3)

                # Submit Form Login dengan ENTER
                _send_keys("{ENTER}", is_raw=False)
                print("[INFO] Form login FRISTA disubmit ({ENTER})")
                time.sleep(0.5)

                # Fallback: tekan TAB lalu ENTER untuk memastikan tombol Login tertekan
                _send_keys("{TAB}", is_raw=False)
                _send_keys("{ENTER}", is_raw=False)

                time.sleep(4.0)  # Tunggu login sukses dan layar utama FRISTA terbuka
            except Exception as err:
                print(f"[ERROR] Gagal melakukan login FRISTA: {err}")
        else:
            print("[INFO] frista_username kosong di config.json, melewati langkah login.")

    # Ketikkan no_peserta ke Layar Utama FRISTA
    main_win = _wait_and_activate(FRISTA_MAIN_TITLES + FRISTA_LOGIN_TITLES, timeout=6.0)
    print(f"[INFO] FRISTA main window for no_peserta input: '{main_win}'")

    if main_win:
        try:
            autoit.win_activate(main_win)
            autoit.win_wait_active(main_win, timeout=5)
            time.sleep(0.5)

            _send_keys("^a{DEL}", is_raw=False)
            _send_keys(no_peserta, is_raw=True)
            print(f"[SUCCESS] FRISTA berhasil dikirim no_peserta: {no_peserta}")
        except Exception as e:
            print(f"[ERROR] Input no_peserta ke FRISTA gagal: {e}")


def start_finger_task(no_peserta: str, config: Config) -> None:
    """
    Tugas otomatisasi background untuk aplikasi Sidik Jari (After.exe).
    - Jika belum jalan / di layar login: buka & login otomatis.
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

    if not already_running:
        print(f"[INFO] Launching Finger process: {config.finger_path}")
        try:
            subprocess.Popen([config.finger_path])
        except Exception as err:
            print(f"[ERROR] Gagal membuka file executable Sidik Jari ({config.finger_path}): {err}")
            return

    # Cek apakah Jendela Login Sidik Jari ada
    login_win = _wait_and_activate(FINGER_LOGIN_TITLES, timeout=12.0)
    print(f"[INFO] Finger login window detected: '{login_win}'")

    if login_win:
        # Kita berada di Layar Login Sidik Jari!
        if config.finger_username:
            print(f"[INFO] Mengisi kredensial Sidik Jari di '{login_win}' untuk user: '{config.finger_username}'")
            try:
                autoit.win_activate(login_win)
                autoit.win_wait_active(login_win, timeout=5)
                time.sleep(0.8)

                # Clear & Isi Username
                _send_keys("^a{DEL}", is_raw=False)
                _send_keys(config.finger_username, is_raw=True)
                time.sleep(0.3)

                # Pindah ke kolom Password
                _send_keys("{TAB}", is_raw=False)
                time.sleep(0.3)

                # Clear & Isi Password
                _send_keys("^a{DEL}", is_raw=False)
                _send_keys(config.finger_password, is_raw=True)
                time.sleep(0.3)

                # Submit Form Login dengan ENTER
                _send_keys("{ENTER}", is_raw=False)
                print("[INFO] Form login Sidik Jari disubmit ({ENTER})")
                time.sleep(0.5)

                _send_keys("{TAB}", is_raw=False)
                _send_keys("{ENTER}", is_raw=False)

                time.sleep(4.0)  # Tunggu login sukses
            except Exception as err:
                print(f"[ERROR] Gagal melakukan login Sidik Jari: {err}")
        else:
            print("[INFO] finger_username kosong di config.json, melewati langkah login.")

    # Ketikkan no_peserta ke Layar Utama Sidik Jari
    main_win = _wait_and_activate(FINGER_MAIN_TITLES + FINGER_LOGIN_TITLES, timeout=6.0)
    print(f"[INFO] Finger main window for no_peserta input: '{main_win}'")

    if main_win:
        try:
            autoit.win_activate(main_win)
            autoit.win_wait_active(main_win, timeout=5)
            time.sleep(0.5)

            _send_keys("^a{DEL}", is_raw=False)
            _send_keys(no_peserta, is_raw=True)
            print(f"[SUCCESS] Aplikasi Sidik Jari berhasil dikirim no_peserta: {no_peserta}")
        except Exception as e:
            print(f"[ERROR] Input no_peserta ke Sidik Jari gagal: {e}")


def stop_frista() -> bool:
    """Menutup aplikasi FRISTA jika sedang berjalan."""
    if not AUTOIT_AVAILABLE:
        print("[MOCK] FRISTA stopped")
        return True

    _configure_autoit()
    try:
        active_pat = _wait_and_activate(FRISTA_LOGIN_TITLES + FRISTA_MAIN_TITLES, timeout=2.0)
        if active_pat:
            autoit.win_close(active_pat)
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
    try:
        active_pat = _wait_and_activate(FINGER_LOGIN_TITLES + FINGER_MAIN_TITLES, timeout=2.0)
        if active_pat:
            autoit.win_close(active_pat)
        autoit.process_close(FINGER_PROCESS)
        print("[INFO] Aplikasi Sidik Jari berhasil dihentikan.")
        return True
    except Exception as e:
        print(f"[WARN] Stop Aplikasi Sidik Jari gagal: {e}")
        return False

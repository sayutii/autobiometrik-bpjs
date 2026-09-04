"""
File titik masuk (entrypoint) saat dijalankan melalui `python -m autobiometrik`.
"""

import sys
from .config import Config
from .server import run_server


def main() -> None:
    print("=" * 60)
    print(" AutoBiometrik BPJS - Local HTTP Bridge Service")
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
        import traceback
        print("\n" + "!" * 60)
        print(" [ERROR CRITICAL] Service gagal berjalan:")
        print("!" * 60)
        traceback.print_exc()
        print("!" * 60)
        input("\nTekan ENTER untuk menutup jendela ini...")
        sys.exit(1)


if __name__ == "__main__":
    main()


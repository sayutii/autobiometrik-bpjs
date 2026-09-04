import threading
from typing import Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

from .config import Config
from .automation import (
    is_autoit_available,
    start_frista_task,
    start_finger_task,
    stop_frista,
    stop_finger,
)
from . import __version__


def create_app(config: Optional[Config] = None) -> Flask:
    """
    Factory function untuk membuat instance aplikasi Flask.
    """
    app = Flask(__name__)
    CORS(app)  # Mengaktifkan CORS untuk semua origin

    cfg = config or Config.load()

    @app.route("/start_frista", methods=["GET"])
    def route_start_frista():
        no_peserta = request.args.get("no_peserta", "").strip()
        if not no_peserta:
            return jsonify({"status": "error", "message": "Parameter no_peserta wajib diisi"}), 400

        # Jalankan otomatisasi di background thread agar tidak memblokir respon HTTP
        thread = threading.Thread(
            target=start_frista_task,
            args=(no_peserta, cfg),
            daemon=True,
        )
        thread.start()

        return jsonify({
            "status": "running",
            "target": "frista",
            "no_peserta": no_peserta,
        })

    @app.route("/start_finger", methods=["GET"])
    def route_start_finger():
        no_peserta = request.args.get("no_peserta", "").strip()
        if not no_peserta:
            return jsonify({"status": "error", "message": "Parameter no_peserta wajib diisi"}), 400

        # Jalankan otomatisasi di background thread
        thread = threading.Thread(
            target=start_finger_task,
            args=(no_peserta, cfg),
            daemon=True,
        )
        thread.start()

        return jsonify({
            "status": "running",
            "target": "finger",
            "no_peserta": no_peserta,
        })

    @app.route("/stop_frista", methods=["GET"])
    def route_stop_frista():
        stop_frista()
        return jsonify({"status": "ok", "message": "FRISTA stopped"})

    @app.route("/stop_finger", methods=["GET"])
    def route_stop_finger():
        stop_finger()
        return jsonify({"status": "ok", "message": "Aplikasi sidik jari stopped"})

    @app.route("/health", methods=["GET"])
    def route_health():
        scheme = "https" if cfg.is_tls_enabled else "http"
        return jsonify({
            "status": "ok",
            "service": "autobiometrik-bpjs",
            "version": __version__,
            "autoit": is_autoit_available(),
            "has_credentials": cfg.has_credentials,
            "has_finger_credentials": cfg.has_finger_credentials,
            "scheme": scheme,
        })

    return app


def run_server(config: Optional[Config] = None) -> None:
    """
    Menjalankan server HTTP/HTTPS AutoBiometrik BPJS.
    """
    cfg = config or Config.load()
    app = create_app(cfg)

    ssl_context = None
    if cfg.is_tls_enabled:
        ssl_context = (cfg.tls_cert, cfg.tls_key)
        print(f"[INFO] Server berjalan menggunakan HTTPS pada {cfg.host}:{cfg.port}")
    else:
        print(f"[INFO] Server berjalan menggunakan HTTP pada {cfg.host}:{cfg.port}")

    app.run(
        host=cfg.host,
        port=cfg.port,
        ssl_context=ssl_context,
        threaded=True,
    )

from __future__ import annotations

from flask import Flask, jsonify


def create_flask_app() -> Flask:
    app = Flask(__name__)

    @app.get("/status")
    def status():
        return jsonify({"service": "flask-sidecar", "status": "ok", "role": "用于兼容插件、小工具、TTS回调或未来独立微服务。"})

    @app.get("/tts/providers")
    def tts_providers():
        return jsonify({"providers": ["placeholder", "azure", "aliyun", "iflytek"], "note": "真实密钥在 env/.env 中配置。"})

    return app

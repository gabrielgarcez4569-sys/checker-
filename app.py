"""Alpha Names server: serves website and performs limited, unauthenticated lookups.

This is an unofficial experimental check; 200 {taken: bool} is the only
remote answer mapped to available/taken. Blocked/ambiguous responses are unknown.
No Discord passwords, user tokens, proxies, or automated account changes.
"""
import os
import re
import time
import threading
from pathlib import Path

import requests
from flask import Flask, jsonify, request, send_file

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2048

DISCORD_ENDPOINT = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
NAME_PATTERN = re.compile(r"^[a-z0-9_.]{2,32}$")
MIN_GAP_SECONDS = 4.0
CACHE_SECONDS = 90.0
last_check_at = 0.0
cache = {}
lock = threading.Lock()


def public_headers(response):
    # GitHub Pages may be hosted on a different origin than this API.
    allowed = os.environ.get("ALLOWED_ORIGIN", "*").strip()
    response.headers["Access-Control-Allow-Origin"] = allowed or "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.after_request
def headers(response):
    if request.path.startswith("/api/"):
        return public_headers(response)
    return response


@app.route("/", methods=["GET"])
def home():
    return send_file(Path(__file__).parent / "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify(ok=True, status="online", note="Não garante que o Discord aceitará as consultas.")


@app.route("/api/check", methods=["OPTIONS"])
def preflight():
    return ("", 204)


@app.route("/api/check", methods=["POST"])
def check():
    global last_check_at
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("username"), str):
        return jsonify(status="unknown", message="Informe username em JSON."), 400
    username = data["username"].strip().lower()
    if len(username) > 32 or not NAME_PATTERN.fullmatch(username) or ".." in username:
        return jsonify(status="invalid", username=username, message="Nome fora das regras básicas do Discord.")

    now = time.monotonic()
    with lock:
        saved = cache.get(username)
        if saved and now - saved[0] < CACHE_SECONDS:
            return jsonify(status=saved[1], username=username, source="discord_unofficial", cached=True)
        elapsed = now - last_check_at
        if last_check_at and elapsed < MIN_GAP_SECONDS:
            return jsonify(status="unknown", message="Intervalo de segurança entre consultas.", retry_after=round(MIN_GAP_SECONDS - elapsed, 1)), 429
        last_check_at = now

    try:
        response = requests.post(
            DISCORD_ENDPOINT,
            json={"username": username},
            headers={"Accept": "application/json", "User-Agent": "AlphaNames/2.0 (username availability check)"},
            timeout=12,
        )
    except requests.RequestException:
        return jsonify(status="unknown", message="Não foi possível conectar ao Discord."), 503

    if response.status_code == 429:
        retry = response.headers.get("Retry-After")
        try:
            retry_after = max(1, min(3600, float(retry))) if retry is not None else 60
        except (TypeError, ValueError):
            retry_after = 60
        return jsonify(status="unknown", message="O Discord limitou as consultas.", retry_after=retry_after), 429
    if response.status_code != 200:
        return jsonify(status="unknown", message="O Discord recusou a consulta ou retornou erro."), 503
    try:
        content = response.json()
    except ValueError:
        return jsonify(status="unknown", message="Resposta inesperada do Discord."), 503
    if not isinstance(content, dict) or type(content.get("taken")) is not bool:
        return jsonify(status="unknown", message="O Discord não retornou o campo 'taken'."), 503
    result = "taken" if content["taken"] else "free"
    with lock:
        cache[username] = (time.monotonic(), result)
        if len(cache) > 2000:
            cutoff = time.monotonic() - CACHE_SECONDS
            for key in list(cache):
                if cache[key][0] < cutoff:
                    del cache[key]
    return jsonify(status=result, username=username, source="discord_unofficial", cached=False, message="Resultado momentâneo; não garante reserva do nome.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))

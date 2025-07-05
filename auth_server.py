# auth_server.py
from flask import Flask, request
import requests
from config import *
from store import save_token
import os

app = Flask(__name__)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    user_id = request.args.get("state")
    if not code or not user_id:
        return "Invalid request."

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }

    r = requests.post("https://accounts.spotify.com/api/token", data=payload)
    token_data = r.json()

    if "access_token" in token_data:
        save_token(user_id, token_data)
        return "✅ Login successful! You can go back to Telegram."
    return "❌ Failed to get token."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # 👈 REQUIRED
    app.run(host="0.0.0.0", port=port)         # 👈 REQUIRED

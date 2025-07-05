from flask import Flask, request
import requests
import os

from config import *
from store import save_token

app = Flask(__name__)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    user_id = request.args.get("state")  # Telegram user ID

    if not code or not user_id:
        return "❌ Invalid request: missing code or user ID."

    # Step 1: Exchange code for access + refresh tokens
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }

    response = requests.post("https://accounts.spotify.com/api/token", data=payload)
    token_data = response.json()

    if "access_token" in token_data:
        # Step 2: Save token to tokens.json
        save_token(user_id, token_data)

        # Step 3: Notify user via Telegram
        telegram_api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        msg = "✅ *Spotify login successful!*\nYou can now use /mytrack and /friends."
        requests.post(telegram_api, data={
            "chat_id": user_id,
            "text": msg,
            "parse_mode": "Markdown"
        })

        return "✅ Spotify login successful! You can return to Telegram."
    else:
        print(f"[ERROR] Token exchange failed: {token_data}")
        return "❌ Failed to get access token from Spotify."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Required by Render
    app.run(host="0.0.0.0", port=port)

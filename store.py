import requests
import json
import os
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

TOKEN_FILE = "tokens.json"
COOKIE_FILE = "cookies.json"

def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        return {}
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

def save_token(user_id, token_data):
    tokens = load_tokens()
    tokens[str(user_id)] = token_data
    save_tokens(tokens)

def get_token(user_id):
    tokens = load_tokens()
    return tokens.get(str(user_id))

def get_valid_token(user_id):
    token_data = get_token(user_id)
    if not token_data:
        return None

    # Try test request to check if access token still works
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}"
    }
    r = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if r.status_code == 401:
        print(f"[INFO] Access token expired for user {user_id}. Refreshing...")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": token_data.get("refresh_token"),
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET
        }

        r = requests.post("https://accounts.spotify.com/api/token", data=payload)
        if r.status_code == 200:
            refreshed = r.json()
            token_data["access_token"] = refreshed["access_token"]

            # Spotify may return a new refresh_token (rare)
            if "refresh_token" in refreshed:
                token_data["refresh_token"] = refreshed["refresh_token"]

            save_token(user_id, token_data)
            return token_data["access_token"]
        else:
            print(f"[ERROR] Failed to refresh token: {r.status_code}, {r.text}")
            return None

    return token_data["access_token"]

# ------------------ FRIENDS ACTIVITY COOKIE SUPPORT ------------------

def load_cookies():
    if not os.path.exists(COOKIE_FILE):
        return {}
    with open(COOKIE_FILE, "r") as f:
        return json.load(f)

def save_cookie(user_id, sp_dc_cookie):
    cookies = load_cookies()
    cookies[str(user_id)] = sp_dc_cookie
    with open(COOKIE_FILE, "w") as f:
        json.dump(cookies, f, indent=2)

def get_cookie(user_id):
    cookies = load_cookies()
    return cookies.get(str(user_id))

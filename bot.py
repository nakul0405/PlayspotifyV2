from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
from config import *
from store import *
import requests
import urllib.parse

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Welcome to PlaySpotify!\nUse /login to connect your Spotify.")

def login(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    scope = "user-read-currently-playing"
    url = (
        "https://accounts.spotify.com/authorize?"
        + urllib.parse.urlencode({
            "client_id": SPOTIFY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "scope": scope,
            "state": user_id
        })
    )
    update.message.reply_text(f"🔗 [Click to Login with Spotify]({url})", parse_mode="Markdown")

def logout(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    delete_token(user_id)
    update.message.reply_text("🚪 Logged out from Spotify.")

def mytrack(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    token_data = get_token(user_id)
    if not token_data:
        update.message.reply_text("❌ Not logged in. Use /login")
        return

    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    res = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)

    if res.status_code != 200:
        update.message.reply_text("⚠️ Could not fetch track. Try re-logging.")
        return

    data = res.json()
    track = data['item']['name']
    artist = data['item']['artists'][0]['name']
    update.message.reply_text(f"🎵 Now playing:\n*{track}* by *{artist}*", parse_mode="Markdown")

def setcookie(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Usage:\n/setcookie your_sp_dc_cookie_here", parse_mode="Markdown")
        return
    cookie = context.args[0]
    save_cookie(update.effective_user.id, cookie)
    update.message.reply_text("✅ Cookie saved.")

def friends(update: Update, context: CallbackContext):
    cookie = get_cookie(update.effective_user.id)
    if not cookie:
        update.message.reply_text("❌ Cookie not set. Use /setcookie.")
        return

    s = requests.Session()
    s.cookies.set("sp_dc", cookie)
    r = s.get("https://spclient.wg.spotify.com/presence-view/v1/buddylist")

    if r.status_code != 200:
        update.message.reply_text("⚠️ Couldn’t fetch friends. Cookie may be invalid.")
        return

    data = r.json()
    msg = "🎧 *Friends Activity:*\n\n"
    for f in data.get("friends", []):
        name = f["user"].get("name", "Unknown")
        track = f.get("track", {}).get("name", "Unknown")
        artist = f.get("track", {}).get("artist", {}).get("name", "")
        msg += f"👤 {name}\n🎵 {track} - {artist}\n\n"

    update.message.reply_text(msg or "No friends active now.", parse_mode="Markdown")

def onlyforadmin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Unauthorized.")
        return
    tokens = load_json("tokens.json")
    msg = "👥 *Logged-in Users:*\n\n"
    for uid in tokens:
        msg += f"🆔 {uid}\n"
    update.message.reply_text(msg, parse_mode="Markdown")

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("login", login))
    dp.add_handler(CommandHandler("logout", logout))
    dp.add_handler(CommandHandler("mytrack", mytrack))
    dp.add_handler(CommandHandler("setcookie", setcookie))
    dp.add_handler(CommandHandler("friends", friends))
    dp.add_handler(CommandHandler("onlyforadmin", onlyforadmin))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
from config import *
from store import *
import requests
import urllib.parse
from store import get_valid_token

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

from store import get_valid_token

@bot.command("mytrack")
def mytrack(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    access_token = get_valid_token(user_id)

    if not access_token:
        update.message.reply_text("⚠️ Could not fetch track. Try re-logging.")
        return

    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)

    if r.status_code == 200:
        data = r.json()
        name = data["item"]["name"]
        artist = data["item"]["artists"][0]["name"]
        update.message.reply_text(f"🎵 You're listening to: *{name}* by *{artist}*", parse_mode="Markdown")
    else:
        update.message.reply_text("⚠️ Nothing is playing right now.")

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

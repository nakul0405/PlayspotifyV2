from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os
import requests
from config import BOT_TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_REDIRECT_URI, ADMIN_ID
from store import get_valid_token, save_cookie, get_cookie, load_tokens

# ------------------ /start ------------------ #
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to *PlaySpotify* bot!\n\n"
        "Use /login to connect your Spotify account 🎧",
        parse_mode="Markdown"
    )

# ------------------ /login ------------------ #
def login(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    auth_url = (
        f"https://accounts.spotify.com/authorize"
        f"?client_id={SPOTIFY_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}"
        f"&scope=user-read-playback-state+user-read-currently-playing"
        f"&state={user_id}"
    )
    update.message.reply_text(f"🔗 Click here to login to Spotify:\n{auth_url}")

# ------------------ /logout ------------------ #
def logout(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    path = "tokens.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        if user_id in data:
            del data[user_id]
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            update.message.reply_text("✅ You’ve been logged out of Spotify.")
        else:
            update.message.reply_text("❌ You were not logged in.")
    else:
        update.message.reply_text("❌ Token store not found.")

# ------------------ /mytrack ------------------ #
def mytrack(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    access_token = get_valid_token(user_id)

    if not access_token:
        update.message.reply_text("⚠️ Could not fetch track. Try /login again.")
        return

    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)

    if r.status_code == 200 and r.json().get("is_playing"):
        data = r.json()
        name = data["item"]["name"]
        artist = data["item"]["artists"][0]["name"]
        update.message.reply_text(f"🎵 You're listening to: *{name}* by *{artist}*", parse_mode="Markdown")
    else:
        update.message.reply_text("😴 Nothing is playing right now.")

# ------------------ /setcookie <cookie> ------------------ #
def setcookie(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not context.args:
        update.message.reply_text("⚠️ Usage: /setcookie <your_sp_dc_cookie>")
        return

    sp_dc = context.args[0]
    save_cookie(user_id, sp_dc)
    update.message.reply_text("✅ Cookie saved successfully!")

# ------------------ /friends ------------------ #
def friends(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sp_dc = get_cookie(user_id)

    if not sp_dc:
        update.message.reply_text("⚠️ Please set your Spotify cookie using /setcookie <cookie>")
        return

    headers = {
        "cookie": f"sp_dc={sp_dc}"
    }
    try:
        r = requests.get("https://guc-spclient.spotify.com/presence-view/v1/buddylist", headers=headers)
        data = r.json()

        if not data.get("friends"):
            update.message.reply_text("🫤 No active friends found.")
            return

        msg = "🎧 *Your Friends' Activity:*\n"
        for friend in data["friends"]:
            name = friend["user"]["name"]
            track = friend["track"]["track"]["name"]
            artist = friend["track"]["track"]["artist"]["name"]
            msg += f"- *{name}*: {track} – {artist}\n"

        update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        update.message.reply_text("❌ Failed to fetch friends activity.")
        print("[ERROR]", e)

# ------------------ /onlyforadmin ------------------ #
def onlyforadmin(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        update.message.reply_text("🚫 You’re not authorized to use this command.")
        return

    tokens = load_tokens()
    if not tokens:
        update.message.reply_text("📭 No users have logged in yet.")
        return

    msg = "🧑‍💻 *Logged-in users:*\n"
    for uid in tokens:
        msg += f"- `{uid}`\n"

    update.message.reply_text(msg, parse_mode="Markdown")

# ------------------ Start the bot ------------------ #
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("login", login))
    dp.add_handler(CommandHandler("logout", logout))
    dp.add_handler(CommandHandler("mytrack", mytrack))
    dp.add_handler(CommandHandler("setcookie", setcookie))
    dp.add_handler(CommandHandler("friends", friends))
    dp.add_handler(CommandHandler("onlyforadmin", onlyforadmin))

    print("✅ Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

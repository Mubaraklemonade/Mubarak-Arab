import os
import threading
from flask import Flask
from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

load_dotenv()

# --- DUMMY FLASK SERVER TO SATISFY RENDER HEALTH CHECKS ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running online!"

def run_flask():
    # Render assigns an environment variable named PORT automatically
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Run Flask on a daemon thread so it listens on a port without blocking the bot
threading.Thread(target=run_flask, daemon=True).start()

# --- TELEGRAM + GEMINI BOT LOGIC ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_KEY)

async def reply_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_message
    )
    await update.message.reply_text(response.text)

if __name__ == "__main__":
    bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_with_gemini))
    bot_app.run_polling()

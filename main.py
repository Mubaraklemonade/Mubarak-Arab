import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from google import genai
import edge_tts

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Download user voice note
    file_id = update.message.voice.file_id
    new_file = await context.bot.get_file(file_id)
    voice_path = "user_voice.ogg"
    await new_file.download_to_drive(voice_path)

    # Send audio directly to Gemini for processing and tutoring response
    audio_file = gemini_client.files.upload(file=voice_path)
    
    system_prompt = (
        "Listen to the spoken Arabic audio carefully. First, transcribe what the user said in Arabic. "
        "Then, act as an Arabic language tutor: briefly correct any grammar or vocabulary mistakes, "
        "explain why, and ask a follow-up question in Arabic with full diacritics (التشكيل) to keep the conversation going."
    )

    gemini_response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[audio_file, system_prompt]
    )
    bot_reply_text = gemini_response.text

    # Convert response to Arabic speech output
    audio_path = "tutor_response.mp3"
    communicate = edge_tts.Communicate(bot_reply_text, "ar-SA-HamedNeural")
    await communicate.save(audio_path)

    # Send text and voice message back in Telegram
    await update.message.reply_text(bot_reply_text, parse_mode="Markdown")
    with open(audio_path, "rb") as out_audio:
        await update.message.reply_voice(voice=out_audio)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()


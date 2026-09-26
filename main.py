import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from google import genai
from groq import Groq
import edge_tts

# Load API Keys from Environment Variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# 1. Handle incoming Voice Messages
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Download the voice note sent by the user
    file_id = update.message.voice.file_id
    new_file = await context.bot.get_file(file_id)
    voice_path = "user_voice.ogg"
    await new_file.download_to_drive(voice_path)

    # Convert Voice to Text using Groq's Whisper API
    with open(voice_path, "rb") as file:
        transcription = groq_client.audio.transcriptions.create(
            file=(voice_path, file.read()),
            model="whisper-large-v3",
            language="ar"
        )
    user_text = transcription.text

    # Prompt Gemini for Arabic Tutoring with Tashkeel
    system_prompt = (
        "You are an Arabic language tutor. Briefly correct any grammar or vocabulary "
        "mistakes in the user's input, explain why, and ask a follow-up question in Arabic "
        "with full diacritics (التشكيل) to keep the conversation going."
    )
    
    gemini_response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{system_prompt}\n\nUser said: {user_text}"
    )
    bot_reply_text = gemini_response.text

    # Convert Gemini's response to Voice Audio (Edge TTS)
    audio_path = "tutor_response.mp3"
    communicate = edge_tts.Communicate(bot_reply_text, "ar-SA-HamedNeural")
    await communicate.save(audio_path)

    # Reply in Telegram with both Text Explanation and Audio Note
    await update.message.reply_text(f"📝 *You said:* {user_text}\n\n{bot_reply_text}", parse_mode="Markdown")
    with open(audio_path, "rb") as audio_file:
        await update.message.reply_voice(voice=audio_file)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import asyncio
import urllib.parse
import requests
from flask import Flask
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip

server = Flask(__name__)

@server.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

TELEGRAM_BOT_TOKEN = "8928062533:AAGg9TLho1hU1Jg8O3jL6o8k9bN1v1m4g1g"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("नमस्ते! मुझे कोई भी कहानी भेजें, मैं पूरी तरह मुफ़्त वीडियो बनाकर भेजूंगा।")

async def generate_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    story = update.message.text
    await update.message.reply_text("कहानी मिल गई! वीडियो तैयार हो रहा है, कृपया 1-2 मिनट प्रतीक्षा करें...")

    loop = asyncio.get_event_loop()

    def process():
        # 1. Generate Voice (Free via gTTS)
        tts = gTTS(text=story, lang='hi')
        tts.save("voice.mp3")

        # 2. Generate Image (Free via Pollinations AI)
        encoded_prompt = urllib.parse.quote(f"{story}, vibrant storybook illustration, detailed, highly aesthetic, 16:9")
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
        
        response = requests.get(img_url, timeout=60)
        with open("scene.jpg", "wb") as f:
            f.write(response.content)

        # 3. Create Video (MoviePy)
        audio = AudioFileClip("voice.mp3")
        duration = audio.duration

        try:
            video = ImageClip("scene.jpg").with_duration(duration).with_audio(audio)
        except AttributeError:
            video = ImageClip("scene.jpg").set_duration(duration).set_audio(audio)

        video.write_videofile("video.mp4", fps=24, codec="libx264", audio_codec="aac")

        # Close clips
        audio.close()
        video.close()

    await loop.run_in_executor(None, process)

    # 4. Send video to user
    with open("video.mp4", "rb") as vid:
        await update.message.reply_video(video=vid, caption="यहाँ आपका वीडियो है! 🎉")

    # Cleanup temporary files
    for file in ["voice.mp3", "scene.jpg", "video.mp4"]:
        if os.path.exists(file):
            try:
                os.remove(file)
            except Exception:
                pass

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_video))
    app.run_polling()

if __name__ == "__main__":
    main()
    

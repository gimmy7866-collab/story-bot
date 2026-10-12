import os, requests
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip

nest_asyncio.apply()

TELEGRAM_BOT_TOKEN = "8928062533:AAFaU5SdY3r54ol7y-VKuvLJPjAjXcsTsJE"
OPENAI_API_KEY = "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"

client = OpenAI(api_key=OPENAI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("नमस्ते! मुझे कोई भी कहानी भेजें, मैं वीडियो बनाकर भेजूंगा।")

async def generate_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    story = update.message.text
    await update.message.reply_text("कहानी मिल गई! वीडियो तैयार हो रहा है, कृपया 1-2 मिनट प्रतीक्षा करें...")

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"कहानी: {story}\nइस पर 2 लाइन का वॉयसओवर हिंदी में और 1 विज़ुअल प्रॉम्प्ट अंग्रेजी में दें।"}]
    )
    text_data = res.choices[0].message.content

    tts = gTTS(text=text_data.split("\n")[0], lang='hi')
    tts.save("voice.mp3")

    img = client.images.generate(model="dall-e-3", prompt=f"Cartoon animation style scene: {story}", size="1024x1024")
    with open("scene.jpg", "wb") as f:
        f.write(requests.get(img.data[0].url).content)

    audio = AudioFileClip("voice.mp3")
    video = ImageClip("scene.jpg").set_duration(audio.duration).set_audio(audio)
    video.write_videofile("video.mp4", fps=24, codec="libx264", audio_codec="aac")

    await update.message.reply_video(video=open("video.mp4", 'rb'))

    os.remove("voice.mp3")
    os.remove("scene.jpg")
    os.remove("video.mp4")

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_video))

print("बॉट चालू हो गया है...")
app.run_polling()

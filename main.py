import os
import re
import json
import asyncio
import urllib.parse
import requests
from flask import Flask
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips
)

# ----------------- FLASK 24/7 SERVER -----------------
server = Flask(__name__)

@server.route('/')
def home():
    return "2D Animation Story Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ----------------- CONFIGURATION -----------------
TELEGRAM_BOT_TOKEN = "8928062533:AAFmg4R7XHOW0rKsYNjaSk6HY5vFUeOENKw"
BG_MUSIC_URL = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3"


def download_bg_music():
    if not os.path.exists("bg_music.mp3"):
        try:
            r = requests.get(BG_MUSIC_URL, timeout=30)
            with open("bg_music.mp3", "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"BG Music error: {e}")


def generate_story_scenes(title):
    system_prompt = (
        "You are an expert 2D animation storyteller. "
        "Create an engaging Hindi moral story based on the title. "
        "Divide it into exactly 3 sequential visual scenes. "
        "Return ONLY a pure valid JSON array of objects with keys: "
        "'scene_no', 'characters', 'visual_prompt', 'narration_hindi'. "
        "'visual_prompt' must be a short descriptive English prompt under 25 words describing the characters and action in 2D cartoon style. "
        "Never include markdown links, brackets, or urls. Return raw JSON array only."
    )
    url = f"https://text.pollinations.ai/{urllib.parse.quote(title)}?system={urllib.parse.quote(system_prompt)}"
    try:
        res = requests.get(url, timeout=45)
        text_resp = res.text.strip()
        text_resp = re.sub(r"^```json\s*", "", text_resp)
        text_resp = re.sub(r"^```\s*", "", text_resp)
        text_resp = re.sub(r"\s*```$", "", text_resp)
        return json.loads(text_resp)
    except Exception:
        return [
            {
                "scene_no": 1,
                "characters": "Main characters",
                "visual_prompt": f"2D cartoon illustration of {title}, colorful Disney animation style",
                "narration_hindi": f"एक समय की बात है, हमारी कहानी की शुरुआत होती है {title} से।"
            },
            {
                "scene_no": 2,
                "characters": "Characters interacting",
                "visual_prompt": f"2D animated cute cartoon scene of {title}, colorful fantasy background",
                "narration_hindi": "कहानी में सभी किरदारों ने मिलकर एक बड़ा फैसला लिया और आगे बढ़े।"
            },
            {
                "scene_no": 3,
                "characters": "Happy ending",
                "visual_prompt": f"2D joyful cartoon ending of {title}, vibrant fairytale vector art",
                "narration_hindi": "अंत में सब कुछ बहुत अच्छा हुआ और कहानी से हमें एक सुंदर सीख मिली।"
            }
        ]


def create_animated_clip(image_path, audio_path):
    audio = AudioFileClip(audio_path)
    audio_duration = audio.duration
    try:
        clip = ImageClip(image_path).with_duration(audio_duration)
        clip = clip.resized(lambda t: 1 + 0.03 * (t / max(audio_duration, 1)))
        clip = clip.with_audio(audio)
    except Exception:
        clip = ImageClip(image_path).set_duration(audio_duration)
        try:
            clip = clip.resize(lambda t: 1 + 0.03 * (t / max(audio_duration, 1)))
        except Exception:
            pass
        clip = clip.set_audio(audio)
    return clip


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎬 *2D एनिमेटेड स्टोरी वीडियो बॉट में आपका स्वागत है!*\n\n"
        "बस मुझे किसी भी कहानी का **शीर्षक (Title)** लिखकर भेजें।\n\n"
        "बॉट अपने आप:\n"
        "✨ किरदार और स्क्रिप्ट चुनेगा\n"
        "🎨 2D कार्टून एनीमेशन सीन बनाएगा\n"
        "🎙️ हिंदी आवाज़ और बैकग्राउंड म्यूज़िक जोड़ेगा\n"
        "📽️ पूरा वीडियो तैयार करके भेजेगा!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def generate_animated_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    status_msg = await update.message.reply_text(f"📖 '{title}' पर 2D स्क्रिप्ट और किरदार तैयार किए जा रहे हैं...")
    loop = asyncio.get_event_loop()

    def process():
        download_bg_music()
        scenes = generate_story_scenes(title)
        video_clips = []
        cleanup_files = []

        for idx, sc in enumerate(scenes):
            scene_num = idx + 1
            narration = sc.get("narration_hindi", title)
            prompt = sc.get("visual_prompt", f"{title} 2D cartoon")

            clean_text = re.sub(r"\[.*?\]\(.*?\)", "", prompt)
            clean_text = re.sub(r"https?://\S+", "", clean_text)
            clean_text = re.sub(r"[^a-zA-Z0-9\s,]", "", clean_text).strip()

            voice_file = f"voice_{scene_num}.mp3"
            tts = gTTS(text=narration, lang='hi')
            tts.save(voice_file)
            cleanup_files.append(voice_file)

            encoded_prompt = urllib.parse.quote(f"{clean_text}, 2D cute animation, flat vector art, Disney Pixar 2d style, bright colors")
            img_url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){encoded_prompt}?width=1280&height=720&nologo=true"

            img_file = f"scene_{scene_num}.jpg"
            img_resp = requests.get(img_url, timeout=60)
            with open(img_file, "wb") as f:
                f.write(img_resp.content)
            cleanup_files.append(img_file)

            clip = create_animated_clip(img_file, voice_file)
            video_clips.append(clip)

        final_video = concatenate_videoclips(video_clips, method="compose")
        total_dur = final_video.duration

        if os.path.exists("bg_music.mp3"):
            try:
                bg_audio = AudioFileClip("bg_music.mp3")
                bg_audio = bg_audio.subclipped(0, min(total_dur, bg_audio.duration))
                try:
                    bg_audio = bg_audio.with_volume_scaled(0.12)
                except AttributeError:
                    bg_audio = bg_audio.volumex(0.12)
                combined_audio = CompositeAudioClip([final_video.audio, bg_audio])
                final_video = final_video.with_audio(combined_audio)
            except Exception as e:
                print(f"BG Music mixing skipped: {e}")

        final_video_file = "story_animation.mp4"
        final_video.write_videofile(final_video_file, fps=24, codec="libx264", audio_codec="aac")
        final_video.close()
        for c in video_clips:
            c.close()

        return final_video_file, cleanup_files, len(scenes)

    await status_msg.edit_text("🎨 2D कार्टून सीन्स, आवाज़ और एनीमेशन रेंडर हो रहा है... (1-2 मिनट प्रतीक्षा करें)")

    try:
        video_path, temp_files, scene_count = await loop.run_in_executor(None, process)
        caption = f"🎬 *शीर्षक:* {title}\n✨ *सीन्स:* {scene_count}\n🎵 बैकग्राउंड म्यूज़िक और हिंदी आवाज़ के साथ!"
        with open(video_path, "rb") as vid:
            await update.message.reply_video(video=vid, caption=caption, parse_mode="Markdown")

        for f in temp_files + [video_path]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
    except Exception as e:
        await update.message.reply_text(f"❌ त्रुटि: {e}")


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_animated_story))
    app.run_polling()


if __name__ == "__main__":
    main()
    

import os
import re
import json
import asyncio
import urllib.parse
import urllib.request
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
    return "Cinematic 2D Story Bot is Active 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ----------------- CONFIGURATION -----------------
TELEGRAM_BOT_TOKEN = "8928062533:AAFlwFvPLyIY-0iQ8FkkyfU9MxgVvgvaY6g"
BG_MUSIC_URL = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3"


def clear_webhook():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=True"
        requests.get(url, timeout=10)
    except Exception:
        pass


def download_bg_music():
    if not os.path.exists("bg_music.mp3"):
        try:
            r = requests.get(BG_MUSIC_URL, timeout=30)
            with open("bg_music.mp3", "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"BG Music Error: {e}")


def clean_text_for_prompt(text):
    if not text:
        return "indian horror spooky house 2d animation"
    # सभी तरह के लिंक्स और ब्रैकेट्स पूरी तरह मिटाना
    text = re.sub(r'https?://\S+', '', str(text))
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s,]', ' ', text)
    words = text.split()
    return " ".join(words[:18])


def generate_story_scenes(title):
    system_prompt = (
        "You are an expert Indian horror 2D cartoon animation writer. "
        "Create an intense Hindi horror story divided into 5 sequential scenes. "
        "Return ONLY a pure valid JSON array of objects with keys: "
        "'scene_no', 'visual_prompt', 'narration_hindi'. "
        "'visual_prompt' must be only 5-10 descriptive English words for a 2D animated scene. "
        "Never include any URLs or markdown code blocks. Output raw JSON only."
    )
    url = f"https://text.pollinations.ai/{urllib.parse.quote(title)}?system={urllib.parse.quote(system_prompt)}"
    try:
        res = requests.get(url, timeout=40)
        raw_text = res.text.strip()
        raw_text = re.sub(r"^```json\s*", "", raw_text)
        raw_text = re.sub(r"^```\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)
        data = json.loads(raw_text)
        if isinstance(data, list) and len(data) > 0:
            return data
    except Exception as e:
        print(f"Script Error: {e}")

    # Fallback High Quality Story
    return [
        {
            "scene_no": 1,
            "visual_prompt": "dark Indian haunted village old haveli full moon night",
            "narration_hindi": f"रात के सन्नाटे में पुरानी हवेली की खामोशी कुछ बयां कर रही थी। कहानी की शुरुआत होती है {title} से।"
        },
        {
            "scene_no": 2,
            "visual_prompt": "spooky wooden door opening dark hallway shadows",
            "narration_hindi": "हवेली का भारी दरवाजा अपने आप खुल गया। अंदर से आने वाली अजीब सी सरसराहट किसी अनहोनी का इशारा दे रही थी।"
        },
        {
            "scene_no": 3,
            "visual_prompt": "creepy glowing red eyes mysterious ghost figure",
            "narration_hindi": "कमरे के अंधेरे कोने में चमकती हुई आंखें नजर आईं। एक रहस्यमयी साया धीरे-धीरे आगे बढ़ रहा था।"
        },
        {
            "scene_no": 4,
            "visual_prompt": "terrified person running suspense atmospheric lighting",
            "narration_hindi": "डर के मारे रोंगटे खड़े हो चुके थे। उस खौफनाक साए से बचने का कोई रास्ता नहीं दिख रहा था।"
        },
        {
            "scene_no": 5,
            "visual_prompt": "morning dawn sunlight falling on quiet mansion",
            "narration_hindi": "सुबह की पहली किरण के साथ ही वो डरावना साया गायब हो गया, पर हवेली का राज हमेशा के लिए दफन रहा।"
        }
    ]


def download_safe_image(prompt_text, save_path):
    """बिना किसी एरर के सुरक्षित 2D इमेज डाउनलोड करना"""
    cleaned = clean_text_for_prompt(prompt_text)
    full_query = f"{cleaned}, 2D indian cartoon animation style, spooky dark atmospheric lighting, high quality vector art"
    encoded = urllib.parse.quote(full_query)
    primary_url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){encoded}?width=1280&height=720&nologo=true"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(primary_url, headers=headers, timeout=50)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(save_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"Pollinations Image Error: {e}")

    # सुरक्षित बैकअप इमेज डाउनलोड (बिना किसी Markdown लिंक के)
    try:
        backup_url = "[https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1280&h=720&fit=crop](https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1280&h=720&fit=crop)"
        r = requests.get(backup_url, headers=headers, timeout=30)
        with open(save_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"Fallback Image Error: {e}")
        return False


def create_animated_clip(image_path, audio_path):
    audio = AudioFileClip(audio_path)
    audio_dur = audio.duration
    try:
        clip = ImageClip(image_path).with_duration(audio_dur)
        clip = clip.resized(lambda t: 1 + 0.03 * (t / max(audio_dur, 1)))
        clip = clip.with_audio(audio)
    except Exception:
        clip = ImageClip(image_path).set_duration(audio_dur)
        try:
            clip = clip.resize(lambda t: 1 + 0.03 * (t / max(audio_dur, 1)))
        except Exception:
            pass
        clip = clip.set_audio(audio)
    return clip


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎬 *2D हॉरर और एनिमेशन स्टोरी ऑटोमेशन*\n\n"
        "मुझे किसी भी कहानी का **टाइटल** भेजें (जैसे: `शापित हवेली का सच` या `डायन का साया`)।\n\n"
        "बॉट स्वतः:\n"
        "📜 पूरी विस्तृत स्क्रिप्ट लिखेगा\n"
        "🎨 2D सिनेमैटिक एनिमेशन सीन्स बनाएगा\n"
        "🎙️ वॉयसओवर और हॉरर बैकग्राउंड म्यूजिक मिक्स करेगा\n"
        "📽️ पूरा वीडियो तैयार करके भेजेगा!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def generate_animated_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    script_msg = await update.message.reply_text(f"📝 '{title}' की पूरी स्क्रिप्ट तैयार की जा रही है...")

    loop = asyncio.get_event_loop()
    scenes = await loop.run_in_executor(None, generate_story_scenes, title)

    script_text = f"📜 *'{title}' की स्क्रिप्ट:*\n\n"
    for sc in scenes:
        script_text += f"🔹 **SCENE {sc.get('scene_no', 1)}:**\n{sc.get('narration_hindi')}\n\n"

    if len(script_text) > 4000:
        script_text = script_text[:3950] + "..."
    await script_msg.edit_text(script_text, parse_mode="Markdown")

    status_msg = await update.message.reply_text("🚀 सभी सीन्स, आवाज़ और वीडियो रेंडर हो रहे हैं... कृपया 2 मिनट प्रतीक्षा करें।")

    def process():
        download_bg_music()
        video_clips = []
        cleanup_files = []

        for idx, sc in enumerate(scenes):
            scene_num = idx + 1
            narration = sc.get("narration_hindi", title)
            prompt = sc.get("visual_prompt", f"{title} 2D horror")

            # 1. Voiceover
            voice_file = f"voice_{scene_num}.mp3"
            tts = gTTS(text=narration, lang='hi')
            tts.save(voice_file)
            cleanup_files.append(voice_file)

            # 2. 2D Scene Image
            img_file = f"scene_{scene_num}.jpg"
            success = download_safe_image(prompt, img_file)
            if success:
                cleanup_files.append(img_file)
                clip = create_animated_clip(img_file, voice_file)
                video_clips.append(clip)

        if not video_clips:
            raise Exception("No video clips generated")

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
                print(f"Audio mix error: {e}")

        final_video_file = "story_animation.mp4"
        final_video.write_videofile(
            final_video_file,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2
        )

        final_video.close()
        for c in video_clips:
            c.close()

        return final_video_file, cleanup_files, len(scenes)

    try:
        video_path, temp_files, scene_count = await loop.run_in_executor(None, process)
        caption = f"🎬 *शीर्षक:* {title}\n✨ *सीन्स:* {scene_count}\n🎵 बैकग्राउंड म्यूजिक व हिंदी आवाज के साथ तैयार!"
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
    clear_webhook()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_animated_story))
    app.run_polling()


if __name__ == "__main__":
    main()
        

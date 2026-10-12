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
from PIL import Image, ImageDraw, ImageFont
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
    return "2D Animation Bot is Running 24/7!"

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
            print(f"BG Music Download Error: {e}")


def generate_story_scenes(title):
    system_prompt = (
        "You are an expert horror 2D cartoon animation writer. "
        "Create an intense Hindi horror story in exactly 4 sequential scenes. "
        "Return ONLY pure JSON array of objects with keys: "
        "'scene_no', 'visual_prompt', 'narration_hindi'. "
        "'visual_prompt' must be strictly short 5 words in English describing cartoon scene. "
        "Raw JSON only, no markdown."
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

    return [
        {
            "scene_no": 1,
            "visual_prompt": "haunted Indian old haveli midnight",
            "narration_hindi": f"रात का गहरा सन्नाटा था। कहानी शुरू होती है {title} से, जहाँ पुरानी हवेली में अजीब सी हलचल महसूस हो रही थी।"
        },
        {
            "scene_no": 2,
            "visual_prompt": "creepy dark room red glowing eyes",
            "narration_hindi": "कमरे के अंधेरे में अचानक एक डरावनी परछाईं दिखाई दी। हवा में ठंडक घुल गई और सब डर से कांपने लगे।"
        },
        {
            "scene_no": 3,
            "visual_prompt": "mysterious ghost floating in darkness",
            "narration_hindi": "उस साए ने धीरे-धीरे हाथ आगे बढ़ाया। खौफ इतना बढ़ गया कि भागने का भी कोई रास्ता नहीं बचा था।"
        },
        {
            "scene_no": 4,
            "visual_prompt": "morning sunlight peaceful old mansion",
            "narration_hindi": "सुबह की पहली किरण के साथ ही वो डरावना साया गायब हो गया और हवेली का रहस्य हमेशा के लिए दफन रहा।"
        }
    ]


def create_fallback_image(text, save_path):
    """अगर AI इमेज फेल हो तो खुद हाई-क्वालिटी विजुअल तैयार करना ताकि एरर न आए"""
    img = Image.new('RGB', (1280, 720), color=(18, 18, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([(40, 40), (1240, 680)], outline=(180, 50, 50), width=6)
    img.save(save_path)


def get_scene_image(prompt_text, save_path):
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', prompt_text).strip()
    words = clean.split()[:8]
    prompt_query = " ".join(words) if words else "horror cartoon haveli"
    full_prompt = f"{prompt_query}, 2D cartoon animation style, Disney Pixar vector art, spooky atmosphere"
    
    encoded = urllib.parse.quote(full_prompt)
    url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){encoded}?width=1280&height=720&nologo=true"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200 and len(r.content) > 4000:
            with open(save_path, "wb") as f:
                f.write(r.content)
            return
    except Exception as e:
        print(f"Pollinations Image Error: {e}")

    # बैकअप इमेज
    try:
        r2 = requests.get("[https://picsum.photos/1280/720](https://picsum.photos/1280/720)", headers=headers, timeout=20)
        if r2.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r2.content)
            return
    except Exception:
        pass

    # अंतिम सुरक्षा: इमेज खुद बनाना
    create_fallback_image(prompt_text, save_path)


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
        "🎬 *2D हॉरर और एनिमेशन स्टोरी बॉट*\n\n"
        "मुझे किसी भी कहानी का **शीर्षक** लिखकर भेजें (उदा. `गुड़िया के अंदर रहने वाली चुड़ैल`)।\n\n"
        "बॉट अपने आप:\n"
        "📜 पूरी कहानी की स्क्रिप्ट बनाएगा\n"
        "🎨 2D एनिमेशन सीन्स तैयार करेगा\n"
        "🎙️ वॉयसओवर व बैकग्राउंड म्यूज़िक जोड़ेगा\n"
        "📽️ पूरा वीडियो बनाकर भेजेगा!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def generate_animated_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    script_msg = await update.message.reply_text(f"📝 '{title}' की विस्तृत स्क्रिप्ट तैयार की जा रही है...")

    loop = asyncio.get_event_loop()
    scenes = await loop.run_in_executor(None, generate_story_scenes, title)

    script_text = f"📜 *'{title}' की स्क्रिप्ट:*\n\n"
    for sc in scenes:
        script_text += f"🔹 **SCENE {sc.get('scene_no', 1)}:**\n{sc.get('narration_hindi')}\n\n"

    if len(script_text) > 4000:
        script_text = script_text[:3950] + "..."
    await script_msg.edit_text(script_text, parse_mode="Markdown")

    status_msg = await update.message.reply_text("🚀 सभी सीन्स, आवाज़ और वीडियो रेंडर हो रहे हैं... कृपया 1-2 मिनट प्रतीक्षा करें।")

    def process():
        download_bg_music()
        video_clips = []
        cleanup_files = []

        for idx, sc in enumerate(scenes):
            scene_num = idx + 1
            narration = sc.get("narration_hindi", title)
            prompt = sc.get("visual_prompt", f"{title} scene")

            # 1. Voice
            voice_file = f"voice_{scene_num}.mp3"
            tts = gTTS(text=narration, lang='hi')
            tts.save(voice_file)
            cleanup_files.append(voice_file)

            # 2. Image
            img_file = f"scene_{scene_num}.jpg"
            get_scene_image(prompt, img_file)
            cleanup_files.append(img_file)

            # 3. Clip
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
        caption = f"🎬 *शीर्षक:* {title}\n✨ *कुल सीन्स:* {scene_count}\n🎵 बैकग्राउंड म्यूज़िक व हिंदी आवाज़ के साथ तैयार!"
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
    

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

# ----------------- FLASK 24/7 KEEP-ALIVE SERVER -----------------
server = Flask(__name__)

@server.route('/')
def home():
    return "2D Animation Story Bot is Running 24/7!"

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
    except Exception as e:
        print(f"Webhook clear error: {e}")


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
        "You are an expert horror/moral story scriptwriter. "
        "Create an engaging Hindi story based on the user's title. "
        "Divide the story into 4 sequential scenes. "
        "Return ONLY a pure valid JSON array of objects with keys: "
        "'scene_no', 'visual_prompt', 'narration_hindi'. "
        "'visual_prompt' must be a short descriptive English prompt under 25 words specifying 2D Indian cartoon animation style, spooky or dramatic lighting. "
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
                "visual_prompt": f"2D horror cartoon style illustration of {title}, dark atmosphere",
                "narration_hindi": f"रात के 9 बजे थे, और कहानी की शुरुआत होती है {title} से।"
            },
            {
                "scene_no": 2,
                "visual_prompt": "2D Indian family home interior, dramatic expressions, cartoon animation style",
                "narration_hindi": "घर के अंदर सब कुछ शांत था, तभी अचानक एक अजीब घटना घटी।"
            },
            {
                "scene_no": 3,
                "visual_prompt": "2D spooky spooky corridor at night, suspenseful cartoon art, high quality",
                "narration_hindi": "डर के मारे सबके हाथ-पैर ठंडे पड़ने लगे, कोई समझ नहीं पा रहा था क्या करें।"
            },
            {
                "scene_no": 4,
                "visual_prompt": "2D dramatic cinematic cartoon ending scene, spooky twist, vector art",
                "narration_hindi": "इस डरावनी घटना ने सबको चौंका दिया और एक नया रहस्य सामने आ गया।"
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
        "🎬 *2D स्टोरी वीडियो ऑटोमेशन बॉट*\n\n"
        "बस मुझे किसी भी कहानी का **शीर्षक (Title)** लिखकर भेजें (उदा. 'चुड़ैल मां', 'रामु की हवेली')।\n\n"
        "बॉट अपने आप:\n"
        "📝 सीन-बाय-सीन स्क्रिप्ट बनाएगा\n"
        "🎨 2D कार्टून एनीमेशन सीन तैयार करेगा\n"
        "🎙️ हिंदी वॉयसओवर और बैकग्राउंड म्यूज़िक जोड़ेगा\n"
        "📽️ पूरा वीडियो बनाकर भेजेगा!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def generate_animated_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    
    # स्टेप 1: पहले स्क्रिप्ट जनरेट करके दिखाना (जैसा वीडियो में देखा)
    script_msg = await update.message.reply_text(f"📝 '{title}' की स्क्रिप्ट तैयार की जा रही है...")
    
    loop = asyncio.get_event_loop()
    scenes = await loop.run_in_executor(None, generate_story_scenes, title)
    
    script_text = f"📜 *'{title}' की स्क्रिप्ट:*\n\n"
    for sc in scenes:
        script_text += f"🔹 **SCENE {sc.get('scene_no', 1)}:**\n{sc.get('narration_hindi')}\n\n"
    
    await script_msg.edit_text(script_text, parse_mode="Markdown")
    
    # स्टेप 2: अब वीडियो रेंडर करना शुरू करना
    status_msg = await update.message.reply_text("🚀 वीडियो जनरेट हो रहा है, कृपया प्रतीक्षा करें...")

    def process():
        download_bg_music()
        video_clips = []
        cleanup_files = []

        for idx, sc in enumerate(scenes):
            scene_num = idx + 1
            narration = sc.get("narration_hindi", title)
            prompt = sc.get("visual_prompt", f"{title} 2D cartoon")

            clean_text = re.sub(r"\[.*?\]\(.*?\)", "", prompt)
            clean_text = re.sub(r"https?://\S+", "", clean_text)
            clean_text = re.sub(r"[^a-zA-Z0-9\s,]", "", clean_text).strip()

            # 1. Voiceover
            voice_file = f"voice_{scene_num}.mp3"
            tts = gTTS(text=narration, lang='hi')
            tts.save(voice_file)
            cleanup_files.append(voice_file)

            # 2. 2D Cartoon Image
            encoded_prompt = urllib.parse.quote(f"{clean_text}, 2D Indian cartoon animation style, storybook vector art, high quality, 16:9")
            img_url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){encoded_prompt}?width=1280&height=720&nologo=true"

            img_file = f"scene_{scene_num}.jpg"
            img_resp = requests.get(img_url, timeout=60)
            with open(img_file, "wb") as f:
                f.write(img_resp.content)
            cleanup_files.append(img_file)

            # 3. Motion Clip
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

    try:
        video_path, temp_files, scene_count = await loop.run_in_executor(None, process)
        caption = f"🎬 *शीर्षक:* {title}\n✨ *सीन्स:* {scene_count}\n🎵 बैकग्राउंड म्यूज़िक और हिंदी आवाज़ के साथ तैयार!"
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

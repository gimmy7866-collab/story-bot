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
    return "Story Bot Engine is Active!"

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
            r = requests.get(BG_MUSIC_URL, timeout=25)
            if r.status_code == 200:
                with open("bg_music.mp3", "wb") as f:
                    f.write(r.content)
        except Exception as e:
            print(f"BG Music Error: {e}")


def generate_story_scenes(title):
    system_prompt = (
        "You are an Indian horror story scriptwriter. "
        "Create an engaging Hindi horror story divided into 4 sequential scenes. "
        "Return ONLY a pure valid JSON array of objects with keys: "
        "'scene_no', 'visual_prompt', 'narration_hindi'. "
        "'visual_prompt' must be descriptive English keywords under 10 words. "
        "Never include markdown or urls. Output raw JSON only."
    )
    url = f"https://text.pollinations.ai/{urllib.parse.quote(title)}?system={urllib.parse.quote(system_prompt)}"
    try:
        res = requests.get(url, timeout=35)
        raw = res.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        if isinstance(data, list) and len(data) > 0:
            return data
    except Exception as e:
        print(f"Script Error: {e}")

    return [
        {
            "scene_no": 1,
            "visual_prompt": "haunted Indian old haveli twilight moonlight scary",
            "narration_hindi": f"सामने एक वीरान और पुरानी हवेली खामोश खड़ी थी। कहानी की शुरुआत होती है {title} से, जहाँ रात को कोई कदम नहीं रखता था।"
        },
        {
            "scene_no": 2,
            "visual_prompt": "creepy dusty antique room cracked mirror red eyes",
            "narration_hindi": "कमरे के अंदर धूल भरी हवा और सन्नाटा था। अचानक टूटे हुए शीशे में दो लाल चमकती आँखें दिखाई दीं।"
        },
        {
            "scene_no": 3,
            "visual_prompt": "dark shadow woman ghost floating atmospheric lighting",
            "narration_hindi": "शीशे से निकलकर एक भयानक साया धीरे-धीरे आगे बढ़ा। कमरे का तापमान एकदम बर्फ जैसा ठंडा हो गया।"
        },
        {
            "scene_no": 4,
            "visual_prompt": "morning sunlight rays falling on haveli peaceful",
            "narration_hindi": "सुबह की पहली किरण पड़ते ही वह खौफनाक साया गायब हो गया, पर हवेली की दास्तान हमेशा के लिए राज़ बन गई।"
        }
    ]


def generate_audio_file(text, file_path):
    """बिना किसी ब्लॉक के स्थिर HTTPS आधारित ऑडियो निर्माण"""
    try:
        tts = gTTS(text=text, lang='hi', slow=False)
        tts.save(file_path)
        return True
    except Exception as e:
        print(f"Audio Error: {e}")
        return False


def download_scene_image(prompt_text, file_path):
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', prompt_text)
    words = clean.split()[:7]
    p_text = " ".join(words) if words else "indian horror haveli"
    full_prompt = f"{p_text}, 2D cartoon animation vector art, dark spooky lighting, cinematic 16:9"
    encoded = urllib.parse.quote(full_prompt)
    url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){encoded}?width=960&height=540&nologo=true"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200 and len(r.content) > 4000:
            with open(file_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"Pollinations Error: {e}")

    # बैकअप विज़ुअल (यदि मुख्य सेवा में देरी हो)
    try:
        backup = requests.get("[https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=960&h=540&fit=crop](https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=960&h=540&fit=crop)", headers=headers, timeout=15)
        if backup.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(backup.content)
            return True
    except Exception:
        pass
    return False


def make_clip(img_path, audio_path):
    audio = AudioFileClip(audio_path)
    dur = audio.duration
    try:
        clip = ImageClip(img_path).with_duration(dur)
        clip = clip.resized(lambda t: 1 + 0.02 * (t / max(dur, 1)))
        clip = clip.with_audio(audio)
    except Exception:
        clip = ImageClip(img_path).set_duration(dur)
        try:
            clip = clip.resize(lambda t: 1 + 0.02 * (t / max(dur, 1)))
        except Exception:
            pass
        clip = clip.set_audio(audio)
    return clip


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎬 *2D स्टोरी वीडियो ऑटोमेशन बॉट*\n\n"
        "मुझे किसी भी कहानी का **टाइटल** भेजें (उदा. `शापित हवेली का सच`)।\n\n"
        "बॉट स्वतः:\n"
        "📜 पूरी कहानी की स्क्रिप्ट लिखेगा\n"
        "🎨 2D सीन तैयार करेगा\n"
        "🎙️ वॉयसओवर व बैकग्राउंड म्यूज़िक जोड़ेगा\n"
        "📽️ पूरा वीडियो रेंडर करके भेजेगा!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def generate_animated_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    status_msg = await update.message.reply_text(f"📝 '{title}' की पूरी स्क्रिप्ट तैयार की जा रही है...")

    loop = asyncio.get_event_loop()
    scenes = await loop.run_in_executor(None, generate_story_scenes, title)

    script_text = f"📜 *'{title}' की स्क्रिप्ट:*\n\n"
    for sc in scenes:
        script_text += f"🔹 **SCENE {sc.get('scene_no')}:**\n{sc.get('narration_hindi')}\n\n"

    await update.message.reply_text(script_text, parse_mode="Markdown")
    await status_msg.edit_text("🎨 सीन्स व ऑडियो तैयार हो रहे हैं... (1/2)")

    def render_process():
        download_bg_music()
        video_clips = []
        cleanup_files = []

        for idx, sc in enumerate(scenes):
            scene_num = idx + 1
            narration = sc.get("narration_hindi", title)
            prompt = sc.get("visual_prompt", title)

            # 1. Voice
            v_file = f"voice_{scene_num}.mp3"
            generate_audio_file(narration, v_file)
            cleanup_files.append(v_file)

            # 2. Image
            i_file = f"scene_{scene_num}.jpg"
            download_scene_image(prompt, i_file)
            cleanup_files.append(i_file)

            # 3. Clip
            clip = make_clip(i_file, v_file)
            video_clips.append(clip)

        final_video = concatenate_videoclips(video_clips, method="compose")
        total_dur = final_video.duration

        if os.path.exists("bg_music.mp3"):
            try:
                bg_audio = AudioFileClip("bg_music.mp3")
                bg_audio = bg_audio.subclipped(0, min(total_dur, bg_audio.duration))
                try:
                    bg_audio = bg_audio.with_volume_scaled(0.10)
                except AttributeError:
                    bg_audio = bg_audio.volumex(0.10)
                combined = CompositeAudioClip([final_video.audio, bg_audio])
                final_video = final_video.with_audio(combined)
            except Exception as e:
                print(f"Mix Error: {e}")

        final_path = "final_story_video.mp4"
        final_video.write_videofile(
            final_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2
        )

        final_video.close()
        for c in video_clips:
            c.close()

        return final_path, cleanup_files

    await status_msg.edit_text("🎞️ वीडियो रेंडरिंग शुरू हो चुकी है... (2/2)")

    try:
        video_path, temp_files = await loop.run_in_executor(None, render_process)
        await status_msg.edit_text("📤 वीडियो Telegram पर भेजा जा रहा है...")

        caption = f"🎬 *शीर्षक:* {title}\n✨ *सीन्स:* {len(scenes)}\n🎵 बैकग्राउंड स्कोर व ऑडियो के साथ तैयार!"
        with open(video_path, "rb") as vid:
            await update.message.reply_video(video=vid, caption=caption, parse_mode="Markdown")

        for f in temp_files + [video_path]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        await status_msg.delete()
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
    

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
    return "2D Animation Story Bot (Long Format) is Running 24/7!"

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


def clean_prompt_text(text):
    """किसी भी तरह के लिंक, ब्रैकेट्स या यूआरएल को पूरी तरह साफ़ करना"""
    if not text:
        return "indian horror cartoon haunted house scene"
    # Remove markdown link [text](url)
    text = re.sub(r'\[.*?\]\(.*?\)', ' ', str(text))
    # Remove raw URLs
    text = re.sub(r'https?://\S+', ' ', text)
    # Remove parentheses, brackets, special symbols
    text = re.sub(r'[^\w\s,]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:120] if text else "spooky Indian 2d animation scene"


def generate_story_scenes(title):
    system_prompt = (
        "You are an expert Indian horror 2D animation story writer. "
        "Create an extensive, detailed multi-part story in Hindi based on the title. "
        "Divide it into 6 sequential dramatic scenes with detailed long narrations. "
        "Return ONLY a pure valid JSON array of objects with keys: "
        "'scene_no', 'visual_prompt', 'narration_hindi'. "
        "'visual_prompt' must be strictly 5 to 10 English words describing the visual scene (NO LINKS, NO URLS). "
        "Return raw JSON only, without markdown code fence."
    )
    url = f"https://text.pollinations.ai/{urllib.parse.quote(title)}?system={urllib.parse.quote(system_prompt)}"
    try:
        res = requests.get(url, timeout=50)
        text_resp = res.text.strip()
        text_resp = re.sub(r"^```json\s*", "", text_resp)
        text_resp = re.sub(r"^```\s*", "", text_resp)
        text_resp = re.sub(r"\s*```$", "", text_resp)
        data = json.loads(text_resp)
        if isinstance(data, list) and len(data) > 0:
            return data
    except Exception as e:
        print(f"Pollinations script error: {e}")

    # फॉलबैक लंबी डिटेल्ड कहानी
    return [
        {
            "scene_no": 1,
            "visual_prompt": "haunted Indian village old mansion moonlight",
            "narration_hindi": f"रात का गहरा सन्नाटा छाया हुआ था। गाँव के किनारे स्थित पुरानी हवेली के बारे में कई कहानियाँ मशहूर थीं। कहानी शुरू होती है {title} से, जहाँ कोई भी रात को जाने की हिम्मत नहीं करता था।"
        },
        {
            "scene_no": 2,
            "visual_prompt": "creepy dark wooden door opening suspense",
            "narration_hindi": "हवेली का भारी और पुराना दरवाजा धीरे से खुला। हवा में एक अजीब सी ठंडक थी और चारों तरफ धूल और जाले लगे हुए थे। हर एक कदम के साथ डर बढ़ता ही जा रहा था।"
        },
        {
            "scene_no": 3,
            "visual_prompt": "mysterious glowing red eyes dark room",
            "narration_hindi": "कमरे के अंधेरे कोने में अचानक दो चमकती हुई लाल आँखें दिखाई दीं। ऐसा लग रहा था मानो कोई साया काफी समय से किसी का इंतज़ार कर रहा हो।"
        },
        {
            "scene_no": 4,
            "visual_prompt": "scary old ghost shadow floating living room",
            "narration_hindi": "वह साया धीरे-धीरे आगे बढ़ा। एक डरावनी और गूंजती हुई आवाज पूरे कमरे में फैल गई। डर के मारे रोंगटे खड़े हो चुके थे और भागने का कोई रास्ता नहीं दिख रहा था।"
        },
        {
            "scene_no": 5,
            "visual_prompt": "dramatic confrontation between character and ghost",
            "narration_hindi": "तभी हिम्मत जुटाकर सच्चाई जानने की कोशिश की गई। पता चला कि वह आत्मा किसी गहरे राज और दुख की वजह से इस पुरानी हवेली में सालों से कैद थी।"
        },
        {
            "scene_no": 6,
            "visual_prompt": "peaceful dawn sunlight falling on old mansion",
            "narration_hindi": "सूरज की पहली किरण के साथ ही सारा अंधेरा और डर समाप्त हो गया। हवेली को हमेशा के लिए उस रहस्यमयी साए से मुक्ति मिल गई।"
        }
    ]


def create_animated_clip(image_path, audio_path):
    audio = AudioFileClip(audio_path)
    audio_dur = audio.duration
    try:
        clip = ImageClip(image_path).with_duration(audio_dur)
        clip = clip.resized(lambda t: 1 + 0.02 * (t / max(audio_dur, 1)))
        clip = clip.with_audio(audio)
    except Exception:
        clip = ImageClip(image_path).set_duration(audio_dur)
        try:
            clip = clip.resize(lambda t: 1 + 0.02 * (t / max(audio_dur, 1)))
        except Exception:
            pass
        clip = clip.set_audio(audio)
    return clip


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎬 *2D स्टोरी वीडियो ऑटोमेशन बॉट*\n\n"
        "बस किसी भी कहानी का **शीर्षक (Title)** लिखकर भेजें (उदा. 'रामु की हवेली या चुड़ैल मां')।\n\n"
        "बॉट अपने आप:\n"
        "📜 पूरी लंबी सीन-बाय-सीन स्क्रिप्ट तैयार करेगा\n"
        "🎨 2D कार्टून एनिमेशन सीन्स बनाएगा\n"
        "🎙️ हिंदी वॉयसओवर और बैकग्राउंड म्यूजिक जोड़ेगा\n"
        "📽️ पूरा वीडियो रेंडर करके भेजेगा!"
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

    # Telegram की मैसेज लिमिट से सुरक्षित रखते हुए स्क्रिप्ट भेजना
    if len(script_text) > 4000:
        script_text = script_text[:3950] + "..."
    await script_msg.edit_text(script_text, parse_mode="Markdown")

    status_msg = await update.message.reply_text("🚀 सभी सीन्स, आवाज़ और वीडियो रेंडर हो रहे हैं... कृपया 2-3 मिनट प्रतीक्षा करें।")

    def process():
        download_bg_music()
        video_clips = []
        cleanup_files = []

        for idx, sc in enumerate(scenes):
            scene_num = idx + 1
            narration = sc.get("narration_hindi", title)
            raw_prompt = sc.get("visual_prompt", f"{title} haunted cartoon")

            # प्रॉम्प्ट को 100% सुरक्षित और साफ़ करना
            cleaned = clean_prompt_text(raw_prompt)
            full_prompt = f"{cleaned}, 2D Indian cartoon animation style, spooky dark atmospheric lighting, Disney Pixar vector art style, high quality"

            # 1. Voiceover
            voice_file = f"voice_{scene_num}.mp3"
            tts = gTTS(text=narration, lang='hi')
            tts.save(voice_file)
            cleanup_files.append(voice_file)

            # 2. Image Download
            img_file = f"scene_{scene_num}.jpg"
            encoded_query = urllib.parse.quote(full_prompt)
            final_img_url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){encoded_query}?width=1280&height=720&nologo=true"

            try:
                res = requests.get(final_img_url, timeout=60)
                if res.status_code == 200 and len(res.content) > 1000:
                    with open(img_file, "wb") as f:
                        f.write(res.content)
                else:
                    raise Exception("Pollinations image fetch failed")
            except Exception:
                # बैकअप इमेज
                fallback = requests.get("[https://picsum.photos/1280/720](https://picsum.photos/1280/720)", timeout=30)
                with open(img_file, "wb") as f:
                    f.write(fallback.content)
            cleanup_files.append(img_file)

            # 3. Clip Creation
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
                print(f"BG Music error: {e}")

        final_video_file = "story_animation.mp4"
        # Render की 512MB RAM पर क्रैश न हो इसलिए ultrafast preset
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
        caption = f"🎬 *शीर्षक:* {title}\n✨ *कुल सीन्स:* {scene_count}\n🎵 बैकग्राउंड म्यूज़िक व हिंदी आवाज़ के साथ!"
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
    

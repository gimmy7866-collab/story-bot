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
import edge_tts
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips
)

# ----------------- FLASK SERVER -----------------
server = Flask(__name__)

@server.route('/')
def home():
    return "Ultra HD 2D Story Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ----------------- CONFIGURATION -----------------
TELEGRAM_BOT_TOKEN = "8928062533:AAFlwFvPLyIY-0iQ8FkkyfU9MxgVvgvaY6g"
BG_MUSIC_URL = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3"

# नेचुरल हिंदी आवाज़ (Microsoft Natural Hindi Voices)
# 'hi-IN-MadhurNeural' (पुरुष की गंभीर आवाज़) या 'hi-IN-SwaraNeural' (महिला की साफ़ आवाज़)
VOICE_NAME = "hi-IN-MadhurNeural"

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
        except Exception:
            pass

async def generate_voice(text, filename):
    """Microsoft Edge-TTS इंसानी आवाज़ जनरेटर"""
    communicate = edge_tts.Communicate(text, VOICE_NAME, rate="-4%", pitch="-2Hz")
    await communicate.save(filename)

def generate_long_story_scenes(title):
    system_prompt = (
        "You are an expert Indian 2D animation story scriptwriter. "
        "Create an engaging, long detailed horror/moral story in Hindi based on the user's title. "
        "Divide the story into 6 detailed scenes (each narration at least 3-4 sentences long). "
        "Return ONLY a pure valid JSON array of objects with keys: "
        "'scene_no', 'visual_prompt', 'narration_hindi'. "
        "'visual_prompt' must be descriptive English keywords under 15 words describing Indian 2D cartoon animation style. "
        "No markdown codeblocks, only raw JSON array."
    )
    url = f"https://text.pollinations.ai/{urllib.parse.quote(title)}?system={urllib.parse.quote(system_prompt)}"
    try:
        res = requests.get(url, timeout=45)
        raw = res.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        if isinstance(data, list) and len(data) > 0:
            return data
    except Exception:
        pass

    return [
        {
            "scene_no": 1,
            "visual_prompt": "creepy abandoned Indian mansion twilight, horror cartoon illustration, 16:9",
            "narration_hindi": f"सामने एक वीरान और पुरानी हवेली खामोश खड़ी थी। गाँव के लोग कहते थे कि रात के समय वहाँ किसी का जाना मौत को दावत देने जैसा है। कहानी शुरू होती है {title} से।"
        },
        {
            "scene_no": 2,
            "visual_prompt": "dusty antique room, cracked mirror, eerie green atmosphere, 2D art",
            "narration_hindi": "कमरे के अंदर धूल भरी हवा और जाले फैले थे। अचानक नजर सामने लगे एक टूटे हुए पुराने शीशे पर पड़ी, जिसमें से अजीब सी रोशनी आ रही थी।"
        },
        {
            "scene_no": 3,
            "visual_prompt": "red glowing sinister eyes in dark hallway, dramatic 2D cartoon",
            "narration_hindi": "शीशे के टुकड़ों में एक भयानक साया मुस्कुराता हुआ दिखाई दिया। उसकी लाल चमकती आँखों ने कमरे के हर कोने में सिहरन पैदा कर दी।"
        },
        {
            "scene_no": 4,
            "visual_prompt": "terrified boy escaping haunted house, suspense cartoon scene",
            "narration_hindi": "तभी एक जोर की चीख गूँज उठी। हवेली के सारे दरवाजे अपने आप बंद होने लगे। डर के मारे रोंगटे खड़े हो चुके थे।"
        },
        {
            "scene_no": 5,
            "visual_prompt": "mysterious ghost woman floating in air, dark Indian folklore art",
            "narration_hindi": "वह आत्मा धीरे-धीरे सामने आई। उसकी दास्तान किसी गहरे धोखे और इंसाफ की पुकार से भरी हुई थी।"
        },
        {
            "scene_no": 6,
            "visual_prompt": "morning sunrise illuminating ancient mansion, cinematic peaceful ending",
            "narration_hindi": "सूरज की किरणें जैसे ही खिड़कियों से अंदर आईं, वह साया हवा में विलीन हो गया। पर उस हवेली की दास्तान गाँव में हमेशा के लिए अमर हो गई।"
        }
    ]

def fetch_hd_image(prompt_text, file_path):
    clean_prompt = re.sub(r'[^a-zA-Z0-9\s,]', '', prompt_text)
    full_prompt = f"{clean_prompt}, 2d indian animation style, cartoon artwork, vibrant cinematic lighting, highly detailed vector illustration, 1080p, 16:9"
    encoded = urllib.parse.quote(full_prompt)
    url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){encoded}?width=1280&height=720&model=flux&nologo=true"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=50)
        if r.status_code == 200 and len(r.content) > 10000:
            with open(file_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass

    # बैकअप 2D एनीमेशन इमेज (ताकि कभी ब्लैक स्क्रीन न आए)
    backup_urls = [
        "[https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1280&h=720&fit=crop](https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1280&h=720&fit=crop)",
        "[https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1280&h=720&fit=crop](https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1280&h=720&fit=crop)"
    ]
    for b_url in backup_urls:
        try:
            r = requests.get(b_url, headers=headers, timeout=20)
            if r.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(r.content)
                return True
        except Exception:
            continue
    return False

def make_clip(img_path, audio_path):
    audio = AudioFileClip(audio_path)
    dur = audio.duration
    try:
        clip = ImageClip(img_path).with_duration(dur)
        clip = clip.resized(lambda t: 1 + 0.03 * (t / max(dur, 1)))
        clip = clip.with_audio(audio)
    except Exception:
        clip = ImageClip(img_path).set_duration(dur)
        try:
            clip = clip.resize(lambda t: 1 + 0.03 * (t / max(dur, 1)))
        except Exception:
            pass
        clip = clip.set_audio(audio)
    return clip

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎬 *प्रोफेशनल 2D स्टोरी वीडियो क्रिएटर बॉट*\n\n"
        "मुझे किसी भी कहानी का **टाइटल** भेजें।\n\n"
        "बॉट का सिस्टम:\n"
        "📜 पूरी लंबी सीन-बाय-सीन स्क्रिप्ट लिखेगा\n"
        "🎙️ **नेचुरल इंसानी आवाज़ (Human-like Voice)** डब करेगा\n"
        "🎨 2D कार्टून एनीमेशन सीन तैयार करेगा\n"
        "📽️ पूरा HD वीडियो बनाकर भेजेगा जिसे आप आगे जोड़ सकते हैं!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def generate_animated_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    script_msg = await update.message.reply_text(f"📝 '{title}' की पूरी कहानी और स्क्रिप्ट लिखी जा रही है...")

    loop = asyncio.get_event_loop()
    scenes = await loop.run_in_executor(None, generate_long_story_scenes, title)

    script_text = f"📜 *'{title}' की पूरी स्क्रिप्ट:*\n\n"
    for sc in scenes:
        script_text += f"🔹 **SCENE {sc.get('scene_no')}:**\n{sc.get('narration_hindi')}\n\n"

    if len(script_text) > 4000:
        script_text = script_text[:3950] + "..."
    await script_msg.edit_text(script_text, parse_mode="Markdown")

    status_msg = await update.message.reply_text("🎙️ इंसानी आवाज़, 2D सीन्स और वीडियो रेंडर हो रहा है... (2-3 मिनट प्रतीक्षा करें)")

    # 1. Voiceover generate करना (Edge-TTS)
    voice_files = []
    for idx, sc in enumerate(scenes):
        v_file = f"voice_{idx+1}.mp3"
        await generate_voice(sc.get("narration_hindi"), v_file)
        voice_files.append(v_file)

    def render_process():
        download_bg_music()
        video_clips = []
        cleanup_files = list(voice_files)

        for idx, sc in enumerate(scenes):
            scene_num = idx + 1
            prompt = sc.get("visual_prompt", f"{title} cartoon scene")
            img_file = f"scene_{scene_num}.jpg"
            
            fetch_hd_image(prompt, img_file)
            cleanup_files.append(img_file)

            clip = make_clip(img_file, voice_files[idx])
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
            except Exception:
                pass

        final_path = "final_story_part.mp4"
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

        return final_path, cleanup_files, len(scenes)

    try:
        video_path, temp_files, count = await loop.run_in_executor(None, render_process)
        caption = f"🎬 *शीर्षक:* {title}\n✨ *सीन्स:* {count}\n🎙️ *आवाज़:* नेचुरल इंसानी हिंदी वॉयसओवर\n🎵 बैकग्राउंड स्कोर के साथ तैयार!"
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
    

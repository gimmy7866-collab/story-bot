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

# ----------------- FLASK SERVER -----------------
server = Flask(__name__)

@server.route('/')
def home():
    return "Multi-Part 15-Minute 2D Story Engine is Running 24/7!"

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
            r = requests.get(BG_MUSIC_URL, timeout=20)
            if r.status_code == 200:
                with open("bg_music.mp3", "wb") as f:
                    f.write(r.content)
        except Exception as e:
            print(f"BG Music Error: {e}")


def generate_full_15min_story(title):
    system_prompt = (
        "You are an expert Indian 2D animation horror storyteller. "
        "Create an extensive 15-minute long Hindi story script based on the title. "
        "Divide the entire story strictly into 3 sequential Parts (Part 1: The Beginning, Part 2: The Mystery Unfolds, Part 3: The Climax & Resolution). "
        "Each part must contain 3 detailed scenes with long descriptive Hindi narrations. "
        "Return ONLY a pure valid JSON array of 3 objects representing the parts. "
        "Format: [ {'part': 1, 'scenes': [ {'scene_no': 1, 'visual_prompt': '...', 'narration_hindi': '...'}, ... ]}, ... ] "
        "No markdown blocks, return raw JSON only."
    )
    url = f"https://text.pollinations.ai/{urllib.parse.quote(title)}?system={urllib.parse.quote(system_prompt)}"
    try:
        res = requests.get(url, timeout=45)
        raw = res.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        if isinstance(data, list) and len(data) == 3:
            return data
    except Exception as e:
        print(f"Script Error: {e}")

    # 15 मिनट की विस्तृत 3-पार्ट्स हॉरर स्क्रिप्ट (बैकअप)
    return [
        {
            "part": 1,
            "title_part": "भाग 1: वीरान हवेली का रहस्य",
            "scenes": [
                {
                    "scene_no": 1,
                    "visual_prompt": "haunted Indian old mansion midnight full moon dark trees",
                    "narration_hindi": f"गाँव के पुराने वीरान रास्ते पर वह हवेली पिछले सौ सालों से खामोश खड़ी थी। रात का गहरा सन्नाटा पसरा हुआ था और हवा में एक अजीब सी ठंडक थी। कहानी की शुरुआत होती है {title} से, जहाँ शाम ढलते ही कोई भी इंसान कदम रखने की हिम्मत नहीं करता था।"
                },
                {
                    "scene_no": 2,
                    "visual_prompt": "creepy wooden haveli entrance door opening slowly dark shadow",
                    "narration_hindi": "अचानक हवेली का भारी पुराना दरवाजा हल्की चरमराती आवाज के साथ अपने आप खुल गया। अंदर की हवा में धूल, जाले और किसी अनजान साए की मौजूदगी साफ़ महसूस हो रही थी। हर बढ़ते कदम के साथ दिल की धड़कनें तेज होती जा रही थीं।"
                },
                {
                    "scene_no": 3,
                    "visual_prompt": "ancient dusty living room antique wooden doll glowing red eyes",
                    "narration_hindi": "कमरे के एक कोने में पुरानी संदूक पर एक प्राचीन गुड़िया रखी हुई थी। उसकी चमकती आँखें मानो सीधे देखने वाले की रूह में झांक रही थीं। तभी हवा में एक हल्की फुसफुसाहट गूँज उठी।"
                }
            ]
        },
        {
            "part": 2,
            "title_part": "भाग 2: आत्मा की दहशत",
            "scenes": [
                {
                    "scene_no": 4,
                    "visual_prompt": "broken antique mirror reflections dark spooky hallway",
                    "narration_hindi": "दीवार पर टंगे टूटे हुए शीशे में एक भयानक परछाईं चलती हुई दिखाई दी। जब मुड़कर देखा तो पीछे कोई नहीं था, पर कमरे की रोशनी लगातार बुझने और जलने लगी।"
                },
                {
                    "scene_no": 5,
                    "visual_prompt": "scary female ghost shadow floating in dark room cinematic",
                    "narration_hindi": "तभी कमरे के अंधेरे में वह खौफनाक साया प्रकट हुआ। उसके बिखरे बाल और उल्टे पैर देखकर किसी के भी होश उड़ जाएं। उसकी दर्दनाक चीख ने पूरी हवेली को हिला कर रख दिया।"
                },
                {
                    "scene_no": 6,
                    "visual_prompt": "terrified character trying to escape trapped inside haveli",
                    "narration_hindi": "हवेली के सारे दरवाजे और खिड़कियां अचानक धड़ाम से बंद हो गईं। भागने का हर रास्ता रुक चुका था और वह साया पल-पल और करीब आता जा रहा था।"
                }
            ]
        },
        {
            "part": 3,
            "title_part": "भाग 3: मुक्ति और अंत",
            "scenes": [
                {
                    "scene_no": 7,
                    "visual_prompt": "ancient scripture talisman burning mystical smoke",
                    "narration_hindi": "तभी याद आया उस पुराने ताबीज और मंत्र का रहस्य, जो उस साए को इस दुनिया के बंधनों से हमेशा के लिए मुक्त कर सकता था। बिना डरे उस गुड़िया के पास जाकर विधि शुरू की गई।"
                },
                {
                    "scene_no": 8,
                    "visual_prompt": "mystical spiritual light dissolving ghost in air",
                    "narration_hindi": "जैसे ही मंत्र पूरा हुआ, हवेली में एक दिव्य तेज रोशनी फैल गई। वह आत्मा अपनी वर्षों पुरानी पीड़ा से मुक्त होकर हवा में विलीन हो गई।"
                },
                {
                    "scene_no": 9,
                    "visual_prompt": "morning sunrise over peaceful haveli clear blue sky",
                    "narration_hindi": "सुबह का सुनहरा सूरज आसमान में चमकने लगा और हवेली से वर्षों का खौफ हमेशा के लिए समाप्त हो गया। इस तरह इस रहस्यमयी दास्तान का अंत हुआ।"
                }
            ]
        }
    ]


def ensure_scene_image(prompt_text, file_path):
    """पक्का करना कि इमेज डिस्क पर 100% बनेगी ताकि No such file एरर कभी न आए"""
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', prompt_text)
    words = clean.split()[:7]
    p_text = " ".join(words) if words else "indian horror cartoon haveli"
    full_prompt = f"{p_text}, 2D cartoon animation vector illustration, Disney Pixar horror style, 16:9 cinematic"
    encoded = urllib.parse.quote(full_prompt)
    url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){encoded}?width=960&height=540&nologo=true"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=25)
        if r.status_code == 200 and len(r.content) > 3000:
            with open(file_path, "wb") as f:
                f.write(r.content)
            return
    except Exception:
        pass

    # बैकअप ऑनलाइन इमेज
    try:
        r2 = requests.get("[https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=960&h=540&fit=crop](https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=960&h=540&fit=crop)", headers=headers, timeout=15)
        if r2.status_code == 200 and len(r2.content) > 2000:
            with open(file_path, "wb") as f:
                f.write(r2.content)
            return
    except Exception:
        pass

    # अंतिम सुरक्षा: इमेज को कोड से खुद ड्रा करना (ताकि फ़ाइल हमेशा मौजूद रहे)
    img = Image.new('RGB', (960, 540), color=(15, 12, 28))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (940, 520)], outline=(180, 40, 40), width=4)
    img.save(file_path)


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
        "🎬 *15-मिनट 2D एनीमेशन स्टोरी बॉट में आपका स्वागत है!*\n\n"
        "बस किसी भी कहानी का **शीर्षक** भेजें (उदा. `गुड़िया के अंदर रहने वाली चुड़ैल`)।\n\n"
        "बॉट स्वतः:\n"
        "📜 पूरी 15-मिनट की 3-पार्ट्स स्क्रिप्ट तैयार करेगा\n"
        "📽️ **Part 1**, **Part 2**, और **Part 3** के अलग-अलग वीडियो रेंडर करके भेजेगा\n"
        "🎙️ हिंदी वॉयसओवर व बैकग्राउंड म्यूज़िक जोड़ेगा!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def generate_animated_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    status_msg = await update.message.reply_text(f"📝 '{title}' की पूरी 15-मिनट की विस्तृत कहानी लिखी जा रही है...")

    loop = asyncio.get_event_loop()
    parts_data = await loop.run_in_executor(None, generate_full_15min_story, title)

    # 1. पूरी स्क्रिप्ट चैट में भेजना
    for part in parts_data:
        p_num = part.get("part", 1)
        p_title = part.get("title_part", f"Part {p_num}")
        text = f"📜 *{p_title}*\n\n"
        for sc in part.get("scenes", []):
            text += f"🔹 **सीन {sc.get('scene_no')}:**\n{sc.get('narration_hindi')}\n\n"
        await update.message.reply_text(text, parse_mode="Markdown")

    await status_msg.edit_text("🚀 अब कहानी के तीनों पार्ट्स (Part 1, 2, 3) के वीडियो रेंडर किए जा रहे हैं...")

    def render_single_part(part_info):
        download_bg_music()
        p_num = part_info.get("part", 1)
        scenes = part_info.get("scenes", [])
        video_clips = []
        cleanup = []

        for idx, sc in enumerate(scenes):
            s_num = sc.get("scene_no", idx + 1)
            narration = sc.get("narration_hindi", title)
            prompt = sc.get("visual_prompt", title)

            # Audio
            v_file = f"voice_p{p_num}_s{s_num}.mp3"
            tts = gTTS(text=narration, lang='hi', slow=False)
            tts.save(v_file)
            cleanup.append(v_file)

            # Image
            i_file = f"scene_p{p_num}_s{s_num}.jpg"
            ensure_scene_image(prompt, i_file)
            cleanup.append(i_file)

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
            except Exception:
                pass

        part_file = f"video_part_{p_num}.mp4"
        final_video.write_videofile(
            part_file,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2
        )

        final_video.close()
        for c in video_clips:
            c.close()

        return part_file, cleanup

    # तीनों पार्ट्स को क्रमबद्ध तरीके से रेंडर करके टेलीग्राम पर भेजना
    for p in parts_data:
        p_num = p.get("part", 1)
        p_title = p.get("title_part", f"Part {p_num}")
        progress_note = await update.message.reply_text(f"⏳ {p_title} का वीडियो रेंडर हो रहा है...")

        try:
            v_path, temp_files = await loop.run_in_executor(None, render_single_part, p)
            caption = f"🎬 *{title}* - {p_title}\n✨ 2D विज़ुअल्स, ऑडियो व म्यूज़िक के साथ तैयार!"
            with open(v_path, "rb") as vid:
                await update.message.reply_video(video=vid, caption=caption, parse_mode="Markdown")

            for f in temp_files + [v_path]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception:
                        pass
            await progress_note.delete()
        except Exception as e:
            await progress_note.edit_text(f"❌ {p_title} में त्रुटि: {e}")

    await status_msg.edit_text("🎉 आपके सभी पार्ट्स के वीडियो सफलतापूर्वक बनाकर भेज दिए गए हैं! आप इन्हें किसी भी एडिटर में जोड़कर पूरी 15 मिनट की फ़िल्म बना सकते हैं।")


def main():
    clear_webhook()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_animated_story))
    app.run_polling()


if __name__ == "__main__":
    main()
            

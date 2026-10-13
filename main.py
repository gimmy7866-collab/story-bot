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
from PIL import Image, ImageDraw
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
    return "Ultra 15-Min 2D Horror Story Engine Active!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ----------------- CONFIGURATION -----------------
TELEGRAM_BOT_TOKEN = "8928062533:AAFlwFvPLyIY-0iQ8FkkyfU9MxgVvgvaY6g"
BG_MUSIC_URL = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3"

# विश्वसनीय 2D हॉरर और एनिमेशन सीन विज़ुअल्स (फ़ॉलबैक के लिए ताकि कभी ब्लैक स्क्रीन न आए)
RELIABLE_SCENE_IMAGES = [
    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=960&h=540&fit=crop",
    "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=960&h=540&fit=crop",
    "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=960&h=540&fit=crop",
    "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=960&h=540&fit=crop"
]

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
        except Exception:
            pass

def generate_full_15min_story(title):
    system_prompt = (
        "You are an expert Indian 2D animation horror storyteller. "
        "Create an extensive 15-minute long Hindi horror story based on the title. "
        "Divide the story strictly into 3 Parts (Part 1: The Beginning, Part 2: The Mystery, Part 3: The Climax). "
        "Each part MUST have 4 long, highly detailed scenes with at least 5-6 descriptive sentences each. "
        "Return ONLY a pure valid JSON array of 3 objects. "
        "Format: [ {'part': 1, 'title_part': 'भाग 1: ...', 'scenes': [ {'scene_no': 1, 'visual_prompt': '...', 'narration_hindi': '...'}, ... ]}, ... ] "
        "No markdown codeblocks, only pure JSON."
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
    except Exception:
        pass

    # विस्तृत 3-पार्ट्स स्क्रिप्ट (लंबी कहानी)
    return [
        {
            "part": 1,
            "title_part": "भाग 1: वीरान हवेली और शापित गुड़िया की शुरुआत",
            "scenes": [
                {
                    "scene_no": 1,
                    "visual_prompt": "spooky Indian haunted mansion dark full moon forest fog",
                    "narration_hindi": f"गाँव के बिल्कुल आखिरी छोर पर वह पुरानी हवेली सदियों से खामोश और वीरान खड़ी थी। गाँव के बड़े-बुजुर्ग कहते थे कि उस हवेली की दीवारों के पीछे एक ऐसा राज़ दफन है, जिसे जो भी छूने की कोशिश करता है, वह कभी वापस नहीं लौटता। कहानी शुरू होती है {title} से। रात के बारह बजते ही वहाँ से अजीब तरह की आवाज़ें आने लगती थीं, मानो कोई अंदर लगातार किसी का इंतज़ार कर रहा हो।"
                },
                {
                    "scene_no": 2,
                    "visual_prompt": "ancient wooden door opening creaking shadows dark entrance",
                    "narration_hindi": "हवेली का भारी और पुराना मुख्य दरवाजा धीरे-धीरे चरमराती हुई डरावनी आवाज़ के साथ अपने आप खुल गया। अंदर की हवा में अजीब सी ठंडक थी, जैसे बर्फ की चादर बिछी हो। चारों तरफ धूल, जाले और टूटे हुए फर्नीचर पड़े थे। हर बढ़ते कदम के साथ दिल की धड़कनें तेज होती जा रही थीं और ऐसा लग रहा था जैसे कोई अदृश्य साया ठीक पीछे चल रहा हो।"
                },
                {
                    "scene_no": 3,
                    "visual_prompt": "creepy porcelain vintage doll sitting antique wooden box red eyes",
                    "narration_hindi": "कमरे के एक धूल भरे कोने में लकड़ी के पुराने बक्से पर एक अजीब सी गुड़िया रखी हुई थी। उसके कपड़े सदियों पुराने थे और उसके चेहरे पर एक खौफनाक मुस्कान खिंची हुई थी। उसकी आँखों में लाल रंग की एक हल्की चमक दिखाई दे रही थी, जो अंधेरे में साफ चमक रही थी। कमरे की हवा अचानक पूरी तरह से थम गई।"
                },
                {
                    "scene_no": 4,
                    "visual_prompt": "doll turning head whispers in darkness eerie atmosphere",
                    "narration_hindi": "अचानक उस गुड़िया की गर्दन हल्की सी घूमी और एक धीमी, फुसफुसाती हुई आवाज़ गूँजी। वह आवाज़ किसी रोते हुए बच्चे की लग रही थी, जो पल भर में एक भयानक चीख में बदल गई। हवेली की पुरानी खिड़कियाँ ज़ोर-ज़ोर से खड़कने लगीं और बाहर चल रही हवा का रुख भी अचानक बदल गया।"
                }
            ]
        },
        {
            "part": 2,
            "title_part": "भाग 2: अंधेरे का साया और आत्मा की दहशत",
            "scenes": [
                {
                    "scene_no": 5,
                    "visual_prompt": "broken mirrors hall reflection shadows moving fast",
                    "narration_hindi": "दीवार पर लगे टूटे हुए शीशों के सामने से गुजरते ही एक खौफनाक मंज़र दिखाई दिया। शीशे में एक काला साया तेजी से भागता हुआ दिखा, लेकिन जब पलटकर देखा गया तो पीछे कोई मौजूद नहीं था। तभी छत से अजीब सी खरोंचने की आवाज़ें आने लगीं, जैसे कोई नुकीले नाखूनों से दीवारों को खुरच रहा हो।"
                },
                {
                    "scene_no": 6,
                    "visual_prompt": "ghostly female figure white saree floating corridor horror",
                    "narration_hindi": "दालान के ठीक बीचों-बीच वह डरावना साया साफ़ दिखने लगा। बिखरे हुए लम्बे बाल, उल्टे पैर और हवा में तैरता हुआ शरीर देखकर रूह कांप उठी। उस आत्मा की आँखों में गहरा दर्द और भयंकर गुस्सा साफ दिखाई दे रहा था। उसने धीरे-धीरे अपनी उंगली उठाकर आगे बढ़ने का इशारा किया।"
                },
                {
                    "scene_no": 7,
                    "visual_prompt": "doors slamming shut trapped in room darkness suspense",
                    "narration_hindi": "हवेली के सारे दरवाजे और खिड़कियाँ एक के बाद एक भयंकर आवाज़ के साथ बंद हो गईं। कमरे में मौजूद सारे दीये और मोमबत्तियाँ बुझ गईं। बाहर निकलने का हर एक रास्ता अब पूरी तरह से बंद हो चुका था और वह डरावना साया दीवारों से उतरकर ठीक सामने फर्श पर खड़ा हो गया।"
                },
                {
                    "scene_no": 8,
                    "visual_prompt": "ancient diary glowing symbols unraveling dark past",
                    "narration_hindi": "तभी ज़मीन पर गिरी एक पुरानी डायरी और तांबे के ताबीज़ पर नज़र पड़ी। उस डायरी के पन्नों में उस आत्मा की दास्तान लिखी थी—वर्षों पहले इस हवेली में उसके साथ हुआ अन्याय ही इस भयंकर शाप का कारण बना था। उस गुड़िया को तोड़कर ही इस भटकती आत्मा को मुक्ति दिलाई जा सकती थी।"
                }
            ]
        },
        {
            "part": 3,
            "title_part": "भाग 3: महा-मुकाबला, मुक्ति और रहस्य का अंत",
            "scenes": [
                {
                    "scene_no": 9,
                    "visual_prompt": "intense ritual fire glowing talisman confrontation ghost",
                    "narration_hindi": "पूरी हिम्मत जुटाकर उस ताबीज़ को उठाया गया और मंत्रोच्चार के साथ उस शापित गुड़िया की ओर कदम बढ़ाए गए। साया गुस्से में पागल हो उठा और पूरी हवेली में तेज़ बर्फीली हवाएं चलने लगीं। चीज़ें हवा में उड़ने लगीं और दीवारों पर दरारें पड़ने लगीं, लेकिन कदम पीछे नहीं हटे।"
                },
                {
                    "scene_no": 10,
                    "visual_prompt": "shattering porcelain doll bright white spiritual light",
                    "narration_hindi": "एक तेज़ वार के साथ उस शापित गुड़िया को फर्श पर पटक कर तोड़ दिया गया। गुड़िया के टूटते ही उसमें से काले धुएं का एक बड़ा गुबार निकला, जो पल भर में एक तेज़ दिव्य सफेद रोशनी में बदलने लगा। उस आत्मा की भयानक चीख अब एक शांत आह में बदल गई।"
                },
                {
                    "scene_no": 11,
                    "visual_prompt": "peaceful spirit ascending into sky dissolving into light",
                    "narration_hindi": "सफेद रोशनी के घेरे में वह साया धीरे-धीरे एक शांत चेहरे में बदल गया। उसने एक अंतिम बार सिर झुकाकर धन्यवाद दिया और आसमान की ओर रोशनी बनकर विलीन हो गया। हवेली की हवा से सारा डर, बदबू और ठंडक हमेशा के लिए समाप्त हो गई।"
                },
                {
                    "scene_no": 12,
                    "visual_prompt": "morning golden sunrise shining over ancient haveli peaceful",
                    "narration_hindi": "सुबह का सुनहरा सूरज बादलों से निकलकर हवेली के आंगन में चमकने लगा। पक्षियों की चहचहाहट ने रात के भयानक सन्नाटे को पूरी तरह मिटा दिया। गाँव के लोगों ने देखा कि सौ सालों का शाप अब हमेशा के लिए खत्म हो चुका था और इस तरह इस रहस्यमयी दास्तान का शांतिपूर्ण अंत हुआ।"
                }
            ]
        }
    ]

def fetch_safe_image(prompt_text, file_path, scene_idx):
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', prompt_text)
    words = clean.split()[:7]
    p_text = " ".join(words) if words else "indian horror cartoon haveli"
    full_prompt = f"{p_text}, 2D cartoon animation vector art, Disney Pixar horror style, vivid colors, 16:9"
    encoded = urllib.parse.quote(full_prompt)
    url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){encoded}?width=854&height=480&nologo=true"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        # कम से कम 10KB की वैध फ़ाइल होनी चाहिए
        if r.status_code == 200 and len(r.content) > 10000:
            with open(file_path, "wb") as f:
                f.write(r.content)
            # सत्यापित करें कि फ़ाइल वाकई एक इमेज है
            with Image.open(file_path) as img:
                img.verify()
            return
    except Exception:
        pass

    # बैकअप ऑनलाइन 2D इमेज (ताकि कभी ब्लैक स्क्रीन न बने)
    backup_url = RELIABLE_SCENE_IMAGES[scene_idx % len(RELIABLE_SCENE_IMAGES)]
    try:
        r2 = requests.get(backup_url, headers=headers, timeout=15)
        if r2.status_code == 200 and len(r2.content) > 5000:
            with open(file_path, "wb") as f:
                f.write(r2.content)
            return
    except Exception:
        pass

    # इमरजेंसी फ़ॉलबैक: एक ग्रेडिएंट विज़ुअल बनाना
    img = Image.new('RGB', (854, 480), color=(25, 20, 45))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (834, 460)], outline=(180, 50, 70), width=6)
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
        "🎬 *15-मिनट 2D एनीमेशन स्टोरी बॉट*\n\n"
        "बस किसी भी कहानी का **शीर्षक** भेजें (उदा. `गुड़िया के अंदर रहने वाली चुड़ैल`)।\n\n"
        "बॉट स्वतः:\n"
        "📜 पूरी 15-मिनट की 3-पार्ट्स स्क्रिप्ट लिखेगा\n"
        "📽️ **भाग 1**, **भाग 2**, और **भाग 3** के अलग-अलग वीडियो रेंडर करके भेजेगा\n"
        "🎨 2D विज़ुअल्स, ऑडियो व बैकग्राउंड म्यूज़िक जोड़ेगा!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def generate_animated_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    status_msg = await update.message.reply_text(f"📝 '{title}' की पूरी 15-मिनट की 3-पार्ट्स कहानी लिखी जा रही है...")

    loop = asyncio.get_event_loop()
    parts_data = await loop.run_in_executor(None, generate_full_15min_story, title)

    # 1. पूरी स्क्रिप्ट चैट में भेजना
    for part in parts_data:
        p_title = part.get("title_part", "भाग")
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

            # Image (पक्का 2D विज़ुअल डाउनलोड)
            i_file = f"scene_p{p_num}_s{s_num}.jpg"
            fetch_safe_image(prompt, i_file, idx)
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

    # तीनों पार्ट्स को रेंडर करके चैट में भेजना
    for p in parts_data:
        p_num = p.get("part", 1)
        p_title = p.get("title_part", f"भाग {p_num}")
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

    await status_msg.edit_text("🎉 तीनों पार्ट्स के वीडियो सफलतापूर्वक भेज दिए गए हैं!")

def main():
    clear_webhook()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_animated_story))
    app.run_polling()

if __name__ == "__main__":
    main()
                                                            

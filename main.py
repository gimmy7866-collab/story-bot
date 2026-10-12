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
        "'visual_prompt' must be a short descriptive English prompt (under 25 words) describing the characters and action in 2D cartoon style. "
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
    duration = audio.
    

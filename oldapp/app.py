import os
import requests
from dotenv import load_dotenv
import base64
import time
import subprocess
from gtts import gTTS

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


# -------- Flash: توليد برومبت سينمائي آمن --------
def generate_prompt(idea):
    url = f"{BASE_URL}/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"حول الفكرة التالية إلى برومبت فيديو سينمائي ومقسم لمشاهد: {idea}"}]}]
    }
    r = requests.post(url, json=payload).json()
    
    candidates = r.get("candidates")
    if not candidates:
        print("❌ لا توجد 'candidates' في الاستجابة")
        print("Full response:", r)
        return None
    
    try:
        return candidates[0]["content"]["parts"][0]["text"]
    except (IndexError, KeyError):
        print("❌ الاستجابة بصيغة غير متوقعة:", r)
        return None


# -------- Gemini: توليد صور --------
def generate_image(prompt, output_file):
    url = f"{BASE_URL}/models/gemini-2.0-flash-exp:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]}
    }
    r = requests.post(url, json=payload).json()
    
    candidates = r.get("candidates")
    if not candidates:
        print("❌ لم يتم توليد صورة:", r)
        return False
    
    for part in candidates[0]["content"]["parts"]:
        if "inlineData" in part:
            image_data = base64.b64decode(part["inlineData"]["data"])
            with open(output_file, "wb") as f:
                f.write(image_data)
            print(f"✅ تم إنشاء الصورة: {output_file}")
            return True
    print("❌ لم يتم العثور على بيانات الصورة في الاستجابة")
    return False


# -------- TTS: توليد تعليق صوتي --------
def generate_voice(text, output_file):
    tts = gTTS(text=text, lang='ar')
    tts.save(output_file)
    print(f"✅ تم إنشاء الصوت: {output_file}")


# -------- FFmpeg: دمج الصور والصوت في فيديو --------
def create_video_from_images(images, audio_file, output_file):
    with open("images.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write("duration 3\n")  # مدة كل صورة 3 ثواني
        f.write(f"file '{images[-1]}'\n")  # آخر صورة بدون duration

    cmd = f"ffmpeg -y -f concat -safe 0 -i images.txt -i {audio_file} -c:v libx264 -c:a aac -shortest {output_file}"
    subprocess.run(cmd, shell=True)
    print(f"✅ تم إنشاء الفيديو النهائي: {output_file}")


# -------- التشغيل --------
if __name__ == "__main__":
    idea = "امرأة يمنية تعمل على الأتمتة وتدير رسائل العملاء"

    print("🎬 توليد البرومبت عبر Flash...")
    prompt = generate_prompt(idea)
    if not prompt:
        exit("❌ فشل توليد البرومبت. تحقق من API Key والموديل.")

    print("Prompt الناتج:\n", prompt)

    # توليد الصور لكل مشهد (مثال 3 مشاهد)
    images = []
    for i in range(1, 4):
        img_file = f"scene_{i}.png"
        success = generate_image(f"{prompt} - مشهد {i}", img_file)
        if success:
            images.append(img_file)

    if not images:
        exit("❌ لم يتم توليد أي صورة")

    # توليد الصوت
    generate_voice(prompt, "voice.mp3")

    # دمج الصور والصوت في فيديو
    create_video_from_images(images, "voice.mp3", "final_video.mp4")

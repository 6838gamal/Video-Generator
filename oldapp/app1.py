import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def generate_preview_video(prompt):
    # هنا نحدد موديل معاينة الفيديو
    model_name = "models/veo-3.1-generate-preview"

    url = f"{BASE_URL}/{model_name}:generateVideo?key={API_KEY}"

    payload = {
        "prompt": {"text": prompt},
        "config": {
            "aspectRatio": "16:9"
        }
    }

    response = requests.post(url, json=payload)
    
    if response.status_code != 200:
        print("❌ خطأ في API:", response.status_code, response.text)
        return None

    data = response.json()
    return data  # سيحتوي على info الفيديو أو رابط المعاينة


if __name__ == "__main__":
    idea = "Muslim woman working on automation in a modern office, cinematic lighting, professional"
    
    print("🎬 توليد معاينة الفيديو...")
    result = generate_preview_video(idea)

    if result:
        # اطبع كل المحتوى لمعرفة الرابط أو التفاصيل
        print("✅ الاستجابة:")
        print(result)

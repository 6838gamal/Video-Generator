import os
import requests
import time
from dotenv import load_dotenv

# -------------------------------
# تحميل مفتاح Runway
# -------------------------------
load_dotenv()
API_KEY = os.getenv("RUNWAY_API_KEY")
if not API_KEY:
    raise ValueError("❌ لم يتم العثور على مفتاح RUNWAY_API_KEY")

BASE_URL = "https://api.dev.runwayml.com/v1"
VIDEO_ENDPOINT = f"{BASE_URL}/video/generate"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-Runway-Version": "2024-11-06"
}

# -------------------------------
# قائمة المخرجين/الأساليب الجاهزة
# -------------------------------
directors_list = [
    "دراماتيكي",
    "كريستوفر نولان",
    "ستيفن سبيلبرغ",
    "واقعي",
    "خيالي",
    "فانتازي",
    "رسوم متحركة",
    "تصوير جوي",
    "سينما قديمة",
    "مستقبلي"
]

print("🎥 اختر أسلوب المخرج أو السينما من القائمة التالية:")
for i, d in enumerate(directors_list, start=1):
    print(f"{i}. {d}")

while True:
    choice = input("أدخل الرقم أو الاسم: ")
    if choice.isdigit() and 1 <= int(choice) <= len(directors_list):
        director = directors_list[int(choice)-1]
        break
    elif choice in directors_list:
        director = choice
        break
    else:
        print("⚠️ اختر رقم أو اسم صالح من القائمة.")

# -------------------------------
# إدخال باقي بيانات الفيديو
# -------------------------------
scene_text = input("\n🎬 أدخل وصف المشهد: ")
duration = int(input("⏱️ مدة الفيديو بالثواني: "))
output_file = input("💾 اسم ملف الإخراج (مع .mp4): ")

final_prompt = f"""
{scene_text}

Directed in style of {director},
cinematic lighting, ultra realistic, dynamic camera
"""

print("\n✨ البرومبت النهائي:")
print(final_prompt)

# -------------------------------
# توليد الفيديو
# -------------------------------
payload = {
    "model": "gen3a_turbo",
    "inputs": {
        "prompt": final_prompt,
        "duration": duration
    }
}

print("\n🎬 جاري إنشاء الفيديو...")

try:
    response = requests.post(VIDEO_ENDPOINT, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"🚨 خطأ API: {response.status_code}")
        print(response.text)
        exit()

    job_id = response.json()["id"]

    while True:
        status_response = requests.get(f"{BASE_URL}/video/{job_id}", headers=headers)
        data = status_response.json()

        if data["status"] == "succeeded":
            video_url = data["output"][0]
            video_data = requests.get(video_url).content
            with open(output_file, "wb") as f:
                f.write(video_data)
            print(f"✅ تم حفظ الفيديو باسم: {output_file}")
            break

        elif data["status"] == "failed":
            print("❌ فشل إنشاء الفيديو")
            break

        else:
            print("⏳ جاري المعالجة...")
            time.sleep(5)

except requests.exceptions.RequestException as e:
    print(f"🚨 خطأ أثناء الاتصال بالـ API: {e}")

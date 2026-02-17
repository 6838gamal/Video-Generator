import os
import requests
from dotenv import load_dotenv

# -------------------------------
# تحميل مفتاح Runway من ملف .env
# -------------------------------
load_dotenv()
API_KEY = os.getenv("RUNWAY_API_KEY")
if not API_KEY:
    raise ValueError("❌ لم يتم العثور على مفتاح RUNWAY_API_KEY")

# ✅ استخدام hostname الصحيح لـ Dev API
BASE_URL = "https://api.dev.runwayml.com/v1"
VIDEO_ENDPOINT = f"{BASE_URL}/video"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-Runway-Version": "2024-11-06"
}

# -------------------------------
# payload تجربة فيديو صغير جدًا
# -------------------------------
test_payload = {
    "model": "gen3a_turbo",
    "prompt": "Test video",
    "duration": 1  # ثانية واحدة فقط للاختبار
}

# -------------------------------
# إرسال الطلب التجريبي
# -------------------------------
try:
    response = requests.post(VIDEO_ENDPOINT, headers=headers, json=test_payload)
    print("Status Code:", response.status_code)
    print("Response:", response.text)

    if response.status_code == 200:
        print("✅ الاتصال ناجح والموديل متاح!")
    elif response.status_code == 401:
        print("❌ خطأ مصادقة! تحقق من API Key أو صلاحياته.")
    elif response.status_code == 403:
        print("❌ الوصول مرفوض! تحقق من صلاحيات الحساب.")
    elif response.status_code == 404:
        print("❌ endpoint غير صحيح! تحقق من URL.")
    else:
        print("⚠️ هناك استجابة غير متوقعة:", response.text)

except requests.exceptions.RequestException as e:
    print("🚨 خطأ اتصال أو Network:", e)

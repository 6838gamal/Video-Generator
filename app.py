import os
import uuid
import time
from fastapi import FastAPI, BackgroundTasks, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from huggingface_hub import InferenceClient

app = FastAPI()
templates = Jinja2Templates(directory="templates")

OUTPUT_DIR = "videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

jobs = {}

# =========================
# إعداد Inference API
# =========================
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN غير محدد. ضع توكن Hugging Face / fal.ai في متغير البيئة HF_TOKEN")

client = InferenceClient(
    provider="fal-ai",
    api_key=HF_TOKEN
)

# =========================
# الصفحة الرئيسية
# =========================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# =========================
# إنشاء مهمة توليد الفيديو
# =========================
@app.post("/generate")
async def generate(background_tasks: BackgroundTasks, prompt: str = Form(...), filename: str = Form(...)):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"progress": 0, "video": None, "filename": filename, "stage": "Waiting"}
    background_tasks.add_task(generate_video_task, job_id, prompt)
    return {"job_id": job_id}

# =========================
# مهمة التوليد مع شريط سلس + تقدير وقت + عرض الأخطاء
# =========================
def generate_video_task(job_id, prompt):
    try:
        # المرحلة 1: إرسال الطلب
        jobs[job_id]["stage"] = "Sending request to fal.ai"
        for i in range(1, 11):
            jobs[job_id]["progress"] = i
            time.sleep(0.2)

        # المرحلة 2: معالجة الفيديو عبر API
        jobs[job_id]["stage"] = "Processing video"
        start_time = time.time()
        video = client.text_to_video(prompt, model="Wan-AI/Wan2.1-T2V-1.3B-Diffusers")
        end_time = time.time()

        # تقدير الوقت للتقدم السلس
        estimated_seconds = max(int(end_time - start_time), 5)
        for i in range(11, 71):
            jobs[job_id]["progress"] = i
            time.sleep(estimated_seconds / 60)

        # المرحلة 3: حفظ الفيديو
        jobs[job_id]["stage"] = "Saving video locally"
        file_name = jobs[job_id]["filename"] + ".mp4"
        file_path = os.path.join(OUTPUT_DIR, file_name)
        with open(file_path, "wb") as f:
            f.write(video)

        # اكتمال العملية
        jobs[job_id]["progress"] = 100
        jobs[job_id]["stage"] = "Completed"
        jobs[job_id]["video"] = file_name

    except Exception as e:
        jobs[job_id]["progress"] = -1
        jobs[job_id]["stage"] = f"{type(e).__name__}: {str(e)}"
        print("Error generating video:", type(e), e)

# =========================
# فحص التقدم
# =========================
@app.get("/progress/{job_id}")
async def progress(job_id: str):
    return jobs.get(job_id, {})

# =========================
# عرض الفيديو
# =========================
@app.get("/video/{file_name}")
async def get_video(file_name: str):
    return FileResponse(os.path.join(OUTPUT_DIR, file_name))

# =========================
# تشغيل السيرفر
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)

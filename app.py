import os
import uuid
import asyncio
import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from huggingface_hub import InferenceClient

app = FastAPI()

templates = Jinja2Templates(directory="templates")

HF_TOKEN = os.getenv("HF_TOKEN")

client = InferenceClient(
    provider="fal-ai",
    api_key=HF_TOKEN,
)

OUTPUT_DIR = "videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# تخزين حالة التقدم
jobs = {}


# -------------------------
# الصفحة الرئيسية
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -------------------------
# إنشاء مهمة توليد فيديو
# -------------------------
@app.post("/generate")
async def generate(prompt: str, background_tasks: BackgroundTasks):

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"progress": 0, "video": None}

    background_tasks.add_task(generate_video_task, job_id, prompt)

    return {"job_id": job_id}


# -------------------------
# مهمة التوليد
# -------------------------
async def generate_video_task(job_id, prompt):

    try:
        jobs[job_id]["progress"] = 20

        file_name = f"{job_id}.mp4"
        file_path = os.path.join(OUTPUT_DIR, file_name)

        video = client.text_to_video(
            prompt,
            model="Wan-AI/Wan2.2-TI2V-5B",
        )

        jobs[job_id]["progress"] = 80

        with open(file_path, "wb") as f:
            f.write(video)

        jobs[job_id]["progress"] = 100
        jobs[job_id]["video"] = file_name

    except:
        jobs[job_id]["progress"] = -1


# -------------------------
# فحص التقدم
# -------------------------
@app.get("/progress/{job_id}")
async def progress(job_id: str):
    return jobs.get(job_id, {})


# -------------------------
# عرض الفيديو
# -------------------------
@app.get("/video/{file_name}")
async def get_video(file_name: str):
    return FileResponse(os.path.join(OUTPUT_DIR, file_name))


# -------------------------
# تشغيل السيرفر
# -------------------------
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

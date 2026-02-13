import os
import uuid
import uvicorn
import torch
from fastapi import FastAPI, BackgroundTasks, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from diffusers import WanPipeline
from diffusers.utils import export_to_video

# =========================
# إعداد FastAPI
# =========================
app = FastAPI()
templates = Jinja2Templates(directory="templates")

OUTPUT_DIR = "videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

jobs = {}

# =========================
# تحميل النموذج مرة واحدة
# =========================
pipe = WanPipeline.from_pretrained(
    "Wan-AI/Wan2.1-T2V-1.3B-Diffusers",
    torch_dtype=torch.float16,
    device_map="auto"
)

# =========================
# الصفحة الرئيسية
# =========================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# =========================
# إنشاء مهمة توليد
# =========================
@app.post("/generate")
async def generate(
    background_tasks: BackgroundTasks,
    prompt: str = Form(...),
    filename: str = Form(...)
):

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "progress": 0,
        "video": None,
        "filename": filename
    }

    background_tasks.add_task(generate_video_task, job_id, prompt)

    return {"job_id": job_id}


# =========================
# مهمة التوليد الحقيقية
# =========================
def generate_video_task(job_id, prompt):

    total_steps = 50

    def progress_callback(step, timestep, latents):
        percent = int((step / total_steps) * 100)
        jobs[job_id]["progress"] = percent

    try:

        frames = pipe(
            prompt=prompt,
            height=480,
            width=832,
            num_frames=81,
            num_inference_steps=total_steps,
            callback=progress_callback,
            callback_steps=1
        ).frames[0]

        file_name = jobs[job_id]["filename"] + ".mp4"
        file_path = os.path.join(OUTPUT_DIR, file_name)

        export_to_video(frames, file_path, fps=16)

        jobs[job_id]["progress"] = 100
        jobs[job_id]["video"] = file_name

    except Exception as e:
        jobs[job_id]["progress"] = -1
        print(e)


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
    uvicorn.run("app:app", host="0.0.0.0", port=8000)

import os
import uuid
import asyncio
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from runwayml import RunwayML

# ===== إعداد Runway =====
client = RunwayML()

# ===== إعداد FastAPI =====
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# تخزين حالة المهام
tasks_status = {}

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# الصفحة الرئيسية
# =========================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# =========================
# بدء توليد الفيديو
# =========================
@app.post("/generate")
async def generate_video(prompt: str = Form(...)):

    task_id = str(uuid.uuid4())
    tasks_status[task_id] = {"status": "starting", "progress": 0}

    asyncio.create_task(run_generation(task_id, prompt))

    return {"task_id": task_id}


# =========================
# تنفيذ التوليد بالخلفية
# =========================
async def run_generation(task_id, prompt):

    try:
        tasks_status[task_id]["status"] = "processing"

        task = client.text_to_video.create(
            model="veo3.1",
            prompt_text=prompt,
            ratio="1280:720",
            duration=8,
        )

        # تتبع التقدم
        while not task.is_done():
            task.poll()
            progress = getattr(task, "progress", 0)
            tasks_status[task_id]["progress"] = progress
            await asyncio.sleep(2)

        output = task.wait_for_task_output()

        video_url = output.output[0]

        # حفظ الفيديو محلياً
        file_path = os.path.join(OUTPUT_DIR, f"{task_id}.mp4")

        import requests
        video_data = requests.get(video_url).content

        with open(file_path, "wb") as f:
            f.write(video_data)

        tasks_status[task_id] = {
            "status": "completed",
            "progress": 100,
            "file": file_path
        }

    except Exception as e:
        tasks_status[task_id] = {
            "status": "error",
            "message": str(e)
        }


# =========================
# جلب حالة المهمة
# =========================
@app.get("/status/{task_id}")
async def get_status(task_id: str):
    return tasks_status.get(task_id, {"status": "unknown"})


# =========================
# تحميل الفيديو
# =========================
@app.get("/download/{task_id}")
async def download_video(task_id: str):

    task = tasks_status.get(task_id)

    if task and task["status"] == "completed":
        return FileResponse(task["file"], filename="video.mp4")

    return JSONResponse({"error": "Video not ready"})


# =========================
# تشغيل السيرفر
# =========================
def main():
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()

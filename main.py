from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from runwayml import RunwayML
import requests
import uuid
import os

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

client = RunwayML()

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ===============================
# تحميل الفيديو
# ===============================
def download_video(url, filename):
    r = requests.get(url)
    with open(filename, "wb") as f:
        f.write(r.content)


# ===============================
# الصفحة الرئيسية
# ===============================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ===============================
# توليد الفيديو
# ===============================
@app.post("/generate")
async def generate(
        request: Request,
        prompt: str = Form(...),
        duration: int = Form(...)
):

    try:

        task = client.text_to_video.create(
            model="veo3.1_fast",
            prompt_text=prompt,
            ratio="1280:720",
            duration=duration,
        ).wait_for_task_output()

        video_url = task.output[0]

        filename = f"{uuid.uuid4()}.mp4"
        filepath = os.path.join(OUTPUT_DIR, filename)

        download_video(video_url, filepath)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "video_file": filename
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": str(e)
            }
        )


# ===============================
# استعراض الفيديو
# ===============================
@app.get("/video/{filename}")
async def get_video(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    return FileResponse(path)


# ===============================
# تحميل الفيديو
# ===============================
@app.get("/download/{filename}")
async def download(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    return FileResponse(path, filename=filename)


# ===============================
# تشغيل السيرفر
# ===============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

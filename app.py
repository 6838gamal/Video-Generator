import os
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from huggingface_hub import InferenceClient

# -------------------------
# إعداد التطبيق
# -------------------------
app = FastAPI()

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("Please set HF_TOKEN environment variable")

client = InferenceClient(
    provider="fal-ai",
    api_key=HF_TOKEN,
)

OUTPUT_DIR = "videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# -------------------------
# Model
# -------------------------
class VideoRequest(BaseModel):
    prompt: str


# -------------------------
# توليد الفيديو
# -------------------------
@app.post("/generate-video")
async def generate_video(request: VideoRequest):

    file_name = f"{uuid.uuid4()}.mp4"
    file_path = os.path.join(OUTPUT_DIR, file_name)

    video = client.text_to_video(
        request.prompt,
        model="Wan-AI/Wan2.2-TI2V-5B",
    )

    with open(file_path, "wb") as f:
        f.write(video)

    return {
        "preview_url": f"http://127.0.0.1:8000/preview/{file_name}",
        "download_url": f"http://127.0.0.1:8000/download/{file_name}"
    }


# -------------------------
# صفحة تشغيل الفيديو
# -------------------------
@app.get("/preview/{file_name}")
async def preview_video(file_name: str):

    html = f"""
    <html>
        <body style="background:black;text-align:center;">
            <video width="720" controls autoplay>
                <source src="/stream/{file_name}" type="video/mp4">
            </video>
        </body>
    </html>
    """

    return HTMLResponse(html)


# -------------------------
# Streaming الفيديو
# -------------------------
@app.get("/stream/{file_name}")
async def stream_video(file_name: str):

    file_path = os.path.join(OUTPUT_DIR, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(404, "Video not found")

    def iterfile():
        with open(file_path, "rb") as f:
            yield from f

    return StreamingResponse(iterfile(), media_type="video/mp4")


# -------------------------
# تحميل الفيديو
# -------------------------
@app.get("/download/{file_name}")
async def download_video(file_name: str):

    file_path = os.path.join(OUTPUT_DIR, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(404, "Video not found")

    return StreamingResponse(
        open(file_path, "rb"),
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )


# -------------------------
# تشغيل السيرفر عبر python app.py
# -------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

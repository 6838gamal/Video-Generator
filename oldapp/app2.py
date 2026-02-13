import os
import subprocess
from gtts import gTTS
from dotenv import load_dotenv
from diffusers import StableDiffusionPipeline
import torch

load_dotenv()

# -------------------------
# 1️⃣ إعداد موديل Stable Diffusion من Hugging Face
# -------------------------
HF_TOKEN = os.getenv("HF_TOKEN")  # ضع توكن Hugging Face في .env
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    use_auth_token=HF_TOKEN,
    torch_dtype=torch.float16
).to("cuda" if torch.cuda.is_available() else "cpu")

# -------------------------
# 2️⃣ توليد الصور لكل مشهد
# -------------------------
def generate_images(prompts, output_folder="scenes"):
    os.makedirs(output_folder, exist_ok=True)
    images = []
    for i, prompt in enumerate(prompts, start=1):
        print(f"🎨 توليد الصورة {i}: {prompt}")
        image = pipe(prompt).images[0]
        filename = os.path.join(output_folder, f"scene_{i}.png")
        image.save(filename)
        images.append(filename)
    return images

# -------------------------
# 3️⃣ توليد تعليق صوتي
# -------------------------
def generate_voice(text, filename="voice.mp3", lang="ar"):
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    print(f"🔊 تم إنشاء الصوت: {filename}")
    return filename

# -------------------------
# 4️⃣ دمج الصور + الصوت → فيديو
# -------------------------
def create_video(images, audio_file, output_file="final_video.mp4", duration_per_image=3):
    with open("images.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {duration_per_image}\n")
        f.write(f"file '{images[-1]}'\n")  # آخر صورة بدون duration

    cmd = f"ffmpeg -y -f concat -safe 0 -i images.txt -i {audio_file} -c:v libx264 -c:a aac -shortest {output_file}"
    subprocess.run(cmd, shell=True)
    print(f"🎬 تم إنشاء الفيديو النهائي: {output_file}")

# -------------------------
# 5️⃣ التشغيل
# -------------------------
if __name__ == "__main__":
    # مثال الفكرة أو البرومبت
    idea = "امرأة يمنية تعمل على الأتمتة وتدير رسائل العملاء، إضاءة سينمائية، مكتب حديث"
    
    # يمكن تقسيم الفكرة إلى عدة مشاهد أو استخدام نفس الفكرة لكل صورة
    prompts = [idea + f", مشهد {i}" for i in range(1, 4)]

    # توليد الصور
    images = generate_images(prompts)

    # توليد الصوت
    audio_file = generate_voice(idea)

    # دمج الصور + الصوت في فيديو
    create_video(images, audio_file)

# import os
# import whisper
# import subprocess
# import uuid
# import re

# def is_valid_youtube_url(url):
#     """Check if URL is a valid YouTube link"""
#     youtube_pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
#     return re.match(youtube_pattern, url)

# def download_youtube_audio(video_url, output_dir="downloads"):
#     """Download audio from a YouTube video using yt-dlp"""
#     if not is_valid_youtube_url(video_url):
#         print("❌ Invalid YouTube URL.")
#         return None

#     os.makedirs(output_dir, exist_ok=True)
#     filename = f"{uuid.uuid4()}.mp3"
#     output_template = os.path.join(output_dir, filename)

#     command = [
#         "yt-dlp",
#         "-x", "--audio-format", "mp3",
#         "-o", output_template,
#         video_url
#     ]

#     print(f"📥 Downloading audio from: {video_url}")
#     try:
#         subprocess.run(command, check=True)
#         print(f"✅ Audio downloaded to: {output_template}")
#         return output_template
#     except subprocess.CalledProcessError as e:
#         print("❌ Error downloading audio:", e)
#         return None

# def transcribe_audio_whisper(audio_path):
#     """Transcribe audio using OpenAI Whisper"""
#     print(f"🧠 Transcribing audio: {audio_path}")
#     model = whisper.load_model("base")  # Choose: tiny, base, small, medium, large
#     result = model.transcribe(audio_path)
#     print("✅ Transcription complete!")
#     return result["text"]

# def main():
#     youtube_url = input("Enter a valid YouTube Video URL: ").strip()

#     audio_file = download_youtube_audio(youtube_url)
#     if audio_file:
#         transcript = transcribe_audio_whisper(audio_file)
#         print("\n📝 Transcript:\n", transcript)

# if __name__ == "__main__":
#     main()
import os
import uuid
import re
import subprocess
import whisper
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
app = FastAPI()

# --------- Data Schema ---------
class YouTubeURLRequest(BaseModel):
    youtube_url: str

# --------- Utility Functions ---------
def is_valid_youtube_url(url: str) -> bool:
    pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
    return re.match(pattern, url) is not None

def download_youtube_audio(video_url: str, output_dir="downloads") -> str:
    if not is_valid_youtube_url(video_url):
        raise ValueError("Invalid YouTube URL.")

    os.makedirs(output_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}.mp3"
    output_template = os.path.join(output_dir, filename)

    command = [
    "yt-dlp",
    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "-x", "--audio-format", "mp3",
    "-o", output_template,
    video_url
]
    print(f"📥 Downloading audio from: {video_url}")
    try:
        subprocess.run(command, check=True)
        return output_template
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to download audio: {e}")

def transcribe_audio_whisper(audio_path: str) -> str:
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]

# --------- FastAPI Route ---------
@app.post("/transcribe")
def transcribe_from_youtube(req: YouTubeURLRequest):
    try:
        audio_path = download_youtube_audio(req.youtube_url)
        transcript = transcribe_audio_whisper(audio_path)
        return {"transcript": transcript}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unexpected error: " + str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))  # Use PORT from Render
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
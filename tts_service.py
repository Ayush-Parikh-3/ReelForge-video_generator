import os
import re
import asyncio
import subprocess
import edge_tts
from config import FFMPEG_PATH, TEMP_DIR, VOICES

def get_audio_duration(audio_path: str) -> float:
    """Extracts exact duration in seconds from an audio file using FFmpeg."""
    cmd = [FFMPEG_PATH, "-i", audio_path]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return 4.0  # safe default fallback

async def generate_speech_async(text: str, voice_id: str, output_path: str, rate: str = "+0%", pitch: str = "+0Hz"):
    """Asynchronously generates speech using Microsoft Edge-TTS."""
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, pitch=pitch)
    await communicate.save(output_path)

def generate_scene_audio(text: str, voice_id: str, output_path: str) -> float:
    """
    Synchronous wrapper to generate scene audio and return exact duration.
    """
    # Clean text of markdown or special symbols
    clean_text = re.sub(r"[*_~`#\[\]]", "", text).strip()
    if not clean_text:
        clean_text = "..."
        
    asyncio.run(generate_speech_async(clean_text, voice_id, output_path))
    duration = get_audio_duration(output_path)
    return duration

def format_srt_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS,mmm string for SRT format."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def generate_scene_srt(text: str, duration: float, output_srt_path: str, max_chars_per_chunk: int = 40):
    """
    Splits scene text into timed subtitle chunks for high readability.
    For short videos, breaks into 3-5 word phrases timed across the scene duration.
    """
    words = text.strip().split()
    if not words:
        words = ["..."]

    # Group words into punchy chunks of 2-3 words for dynamic video pacing
    chunks = []
    chunk_size = 3
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)

    chunk_count = len(chunks)
    chunk_duration = duration / chunk_count

    srt_entries = []
    for idx, chunk in enumerate(chunks):
        start_t = idx * chunk_duration
        end_t = min(duration, (idx + 1) * chunk_duration)
        srt_entries.append(
            f"{idx + 1}\n{format_srt_time(start_t)} --> {format_srt_time(end_t)}\n{chunk}\n"
        )

    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries) + "\n")

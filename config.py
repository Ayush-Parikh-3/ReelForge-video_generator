import os
import shutil
import imageio_ffmpeg

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Ensure required directories exist
for directory in [STATIC_DIR, OUTPUT_DIR, TEMP_DIR, ASSETS_DIR]:
    os.makedirs(directory, exist_ok=True)

def get_ffmpeg_executable():
    """Finds FFmpeg on system PATH or falls back to bundled imageio-ffmpeg."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_executable()

# Also inject ffmpeg directory into system PATH so any subprocess can find it
ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
if ffmpeg_dir and ffmpeg_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# Available Edge-TTS Neural Voices
VOICES = [
    {"id": "en-US-ChristopherNeural", "name": "Christopher (US Male - Deep & Authoritative)", "gender": "male", "lang": "en-US"},
    {"id": "en-US-GuyNeural", "name": "Guy (US Male - Casual & Engaging)", "gender": "male", "lang": "en-US"},
    {"id": "en-US-JennyNeural", "name": "Jenny (US Female - Warm & Expressive)", "gender": "female", "lang": "en-US"},
    {"id": "en-US-AriaNeural", "name": "Aria (US Female - Clear & Professional)", "gender": "female", "lang": "en-US"},
    {"id": "en-GB-RyanNeural", "name": "Ryan (UK Male - Cinematic Documentary)", "gender": "male", "lang": "en-GB"},
    {"id": "en-GB-SoniaNeural", "name": "Sonia (UK Female - Elegant & Storyteller)", "gender": "female", "lang": "en-GB"},
    {"id": "en-IN-MadhurNeural", "name": "Madhur (Indian Male - Clear & Dynamic)", "gender": "male", "lang": "en-IN"},
    {"id": "en-IN-SwaraNeural", "name": "Swara (Indian Female - Friendly & Clear)", "gender": "female", "lang": "en-IN"},
    {"id": "es-ES-AlvaroNeural", "name": "Alvaro (Spanish Male - Narrative)", "gender": "male", "lang": "es-ES"},
    {"id": "fr-FR-HenriNeural", "name": "Henri (French Male - Smooth & Rich)", "gender": "male", "lang": "fr-FR"},
    {"id": "de-DE-ConradNeural", "name": "Conrad (German Male - Deep & Confident)", "gender": "male", "lang": "de-DE"},
    {"id": "ja-JP-KeitaNeural", "name": "Keita (Japanese Male - Engaging)", "gender": "male", "lang": "ja-JP"},
]

# Visual Styles Presets
STYLES = {
    "cinematic": "cinematic lighting, photorealistic 8k, dramatic atmosphere, anamorphic lens flare, award winning photography, ultra-detailed",
    "anime": "vibrant anime illustration style, Makoto Shinkai aesthetic, gorgeous sky, emotional lighting, high detail digital art",
    "cyberpunk": "cyberpunk aesthetic, glowing neon lights, dark rainy city, reflective surfaces, volumetric fog, futuristic",
    "documentary": "National Geographic documentary photography, crisp focus, natural lighting, high dynamic range, authentic photojournalism",
    "fantasy": "epic fantasy concept art, magical glowing runes, ethereal atmosphere, mystical environment, Greg Rutkowski style",
    "minimalist": "minimalist modern 3D render, soft pastel lighting, clean isometric aesthetic, high quality studio lighting",
    "vintage": "vintage 1970s film photograph, retro 35mm grain, warm sepia tones, nostalgic Kodachrome aesthetic"
}

# Video Dimension presets
DIMENSIONS = {
    "16:9": {"width": 1280, "height": 720, "label": "Landscape (YouTube / Web)"},
    "9:16": {"width": 720, "height": 1280, "label": "Portrait (TikTok / Shorts / Reels)"}
}

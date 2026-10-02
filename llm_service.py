import os
import re
import json
import random
import logging
import requests
from config import STYLES

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a master viral video producer and cinematic visual director.
Given a topic, you MUST create an engaging short video script divided into distinct scenes.

CRITICAL INSTRUCTIONS:
1. You MUST generate EXACTLY the number of scenes requested.
2. For each scene:
   - "scene_id": integer (1, 2, 3, etc.)
   - "narration": Punchy, gripping spoken narration (15-25 words, ~4-6 seconds).
   - "visual_prompt": A highly specific visual description that MATCHES THE NARRATION EXACTLY. Describe the physical subject, camera angle, action, lighting, environment, and atmosphere so an AI image generator produces the perfect visual for this exact moment. Avoid vague words; describe visible objects, colors, and camera framing.
   - "subtitle_text": Exact subtitle line (short & punchy).

Return ONLY valid JSON matching this schema:
{
  "title": "Compelling Video Title",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "First scene narration...",
      "visual_prompt": "Specific visual description matching the first scene...",
      "subtitle_text": "Short subtitle line"
    }
  ]
}
Do NOT include any commentary outside the JSON block.
"""

def clean_json_response(raw_text: str) -> dict:
    """Extract and parse JSON from LLM response text, with regex rescue if needed."""
    text = raw_text.strip()
    
    # Try finding markdown code block
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end+1]
            
    # Fix potential trailing commas
    text_clean = re.sub(r",\s*([\]}])", r"\1", text)
    
    try:
        return json.loads(text_clean)
    except Exception:
        pass

    # Regex extraction fallback: find all scene blocks
    title_m = re.search(r'"title"\s*:\s*"([^"]+)"', text)
    title = title_m.group(1) if title_m else "Untitled Story"
    
    # Extract scenes individually
    scene_pattern = re.compile(
        r'\{\s*"scene_id"\s*:\s*(\d+)[\s\S]*?"narration"\s*:\s*"([^"]+)"[\s\S]*?"visual_prompt"\s*:\s*"([^"]+)"(?:[\s\S]*?"subtitle_text"\s*:\s*"([^"]*)")?[\s\S]*?\}',
        re.DOTALL
    )
    scenes = []
    for m in scene_pattern.finditer(text):
        s_id = int(m.group(1))
        narr = m.group(2).replace('\\"', '"')
        vis = m.group(3).replace('\\"', '"')
        sub = m.group(4).replace('\\"', '"') if m.group(4) else narr
        scenes.append({
            "scene_id": s_id,
            "narration": narr,
            "visual_prompt": vis,
            "subtitle_text": sub
        })
        
    if scenes:
        return {"title": title, "scenes": scenes}
        
    raise ValueError(f"Could not parse valid scenes from LLM response")

def generate_script_gemini(prompt: str, scene_count: int, style: str, api_key: str) -> dict:
    """Generate script using Google Gemini Free API."""
    style_desc = STYLES.get(style, STYLES["cinematic"])
    user_msg = f"""Topic/Prompt: "{prompt}"
REQUIRED SCENE COUNT: EXACTLY {scene_count} scenes (Numbered 1 to {scene_count}).
Visual Style: {style} ({style_desc})
Write a gripping script with EXACTLY {scene_count} scenes. Make visual prompts match each scene's narration precisely. Return valid JSON only."""

    models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]
    last_err = None

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{user_msg}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "response_mime_type": "application/json"
            }
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return clean_json_response(text)
            else:
                last_err = f"Gemini error {resp.status_code}: {resp.text}"
        except Exception as e:
            last_err = str(e)
            continue
            
    raise RuntimeError(f"Gemini API request failed: {last_err}")

def generate_script_pollinations(prompt: str, scene_count: int, style: str) -> dict:
    """Generate script using Free Pollinations Text API (No API Key Required)."""
    style_desc = STYLES.get(style, STYLES["cinematic"])
    user_msg = f"""Topic/Prompt: "{prompt}"
MANDATORY: You MUST generate EXACTLY {scene_count} distinct scenes, numbered 1 to {scene_count}.
Visual Style: {style} ({style_desc})
Ensure each visual_prompt vividly and specifically depicts the exact event happening in that scene's narration.
Return valid JSON only."""

    url = "https://text.pollinations.ai/"
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        "jsonMode": True,
        "seed": random.randint(100, 99999)
    }
    
    resp = requests.post(url, json=payload, timeout=35)
    if resp.status_code == 200:
        return clean_json_response(resp.text)
    raise RuntimeError(f"Free Pollinations Text API error {resp.status_code}: {resp.text}")

def generate_script_fallback(prompt: str, scene_count: int, style: str) -> dict:
    """Dynamic fallback script generator ensuring exact scene count."""
    style_desc = STYLES.get(style, STYLES["cinematic"])
    title = prompt.strip().capitalize()
    if len(title) > 40:
        title = title[:37] + "..."

    # Pre-crafted dynamic scene concepts
    story_templates = [
        {
            "narration": f"Have you ever wondered about {prompt}? Here is the incredible truth.",
            "visual": f"A dramatic establishing cinematic shot of {prompt}, mysterious atmosphere, volumetric lighting, 8k resolution"
        },
        {
            "narration": f"Beneath the surface lies a hidden structure that science is only beginning to understand.",
            "visual": f"A close-up revealing intricate inner workings of {prompt}, glowing circuits and energy pathways, high detail"
        },
        {
            "narration": f"Every single detail connects to a much larger picture, revealing secrets hidden in plain sight.",
            "visual": f"A wide expansive panorama showing the full scale of {prompt}, golden hour lighting, cinematic composition"
        },
        {
            "narration": f"When you look closer, the complexity defies imagination, transforming before our eyes.",
            "visual": f"Macro detailed view of {prompt} actively operating, dynamic motion particles, crisp focus"
        },
        {
            "narration": f"As modern discoveries continue to emerge, our understanding of {prompt} evolves every day.",
            "visual": f"Futuristic laboratory view researching {prompt}, holographic displays, sleek modern technology"
        },
        {
            "narration": f"The future is unfolding faster than ever, and this is only the beginning of what is possible.",
            "visual": f"Breathtaking futuristic horizon inspired by {prompt}, glowing neon skyline, inspiring sunrise"
        },
        {
            "narration": f"Think about how far we have come, and where this breakthrough will take humanity next.",
            "visual": f"Inspirational wide view of explorers and scientists studying {prompt}, warm cinematic backlight"
        },
        {
            "narration": f"Remember, reality is often far more fascinating than fiction. What do you think?",
            "visual": f"Iconic cinematic portrait shot symbolizing {prompt}, dramatic contrast, award winning photography"
        }
    ]
    
    scenes = []
    for i in range(scene_count):
        idx = i % len(story_templates)
        template = story_templates[idx]
        scenes.append({
            "scene_id": i + 1,
            "narration": template["narration"],
            "visual_prompt": f"{template['visual']}, {style_desc}",
            "subtitle_text": template["narration"]
        })

    return {
        "title": title,
        "scenes": scenes
    }

def ensure_exact_scene_count(script_data: dict, target_count: int, prompt: str, style: str) -> dict:
    """Guarantees that the returned script contains EXACTLY target_count scenes."""
    scenes = script_data.get("scenes", [])
    title = script_data.get("title", prompt.capitalize())
    style_desc = STYLES.get(style, STYLES["cinematic"])

    if len(scenes) >= target_count:
        # Trim to exact target count and ensure sequential scene_id
        script_data["scenes"] = scenes[:target_count]
        for idx, s in enumerate(script_data["scenes"]):
            s["scene_id"] = idx + 1
        return script_data

    # If LLM returned fewer scenes, pad with context-aware scenes
    needed = target_count - len(scenes)
    logger.info(f"LLM produced {len(scenes)} scenes. Auto-extending by {needed} scenes to match target {target_count}...")
    
    fallback_data = generate_script_fallback(prompt, target_count, style)
    fallback_scenes = fallback_data["scenes"]

    for i in range(len(scenes), target_count):
        scenes.append(fallback_scenes[i])

    for idx, s in enumerate(scenes):
        s["scene_id"] = idx + 1

    script_data["scenes"] = scenes
    return script_data

def generate_script(prompt: str, scene_count: int = 4, style: str = "cinematic", api_key: str = None) -> dict:
    """
    Main entry point for script generation.
    Strictly guarantees that EXACTLY scene_count scenes are returned.
    """
    scene_count = max(2, min(scene_count, 8))
    result = None

    if api_key and api_key.strip():
        try:
            logger.info("Attempting script generation with user Gemini API Key...")
            result = generate_script_gemini(prompt, scene_count, style, api_key.strip())
        except Exception as e:
            logger.warning(f"Gemini API failed: {e}. Falling back to free Pollinations API...")
            
    if not result:
        try:
            logger.info("Generating script with Free Pollinations Text API...")
            result = generate_script_pollinations(prompt, scene_count, style)
        except Exception as e:
            logger.warning(f"Pollinations text API failed: {e}. Using generative fallback...")

    if not result or not result.get("scenes"):
        result = generate_script_fallback(prompt, scene_count, style)

    # Strictly guarantee exact scene count
    return ensure_exact_scene_count(result, scene_count, prompt, style)

import os
import time
import uuid
import json
import logging
from config import TEMP_DIR, OUTPUT_DIR
from llm_service import generate_script
from tts_service import generate_scene_audio, generate_scene_srt
from image_service import generate_scene_image
from video_service import render_scene_clip, assemble_full_video

logger = logging.getLogger(__name__)

# In-memory job status store
JOBS = {}

def update_job_status(job_id: str, stage: str, progress: int, message: str, data: dict = None):
    """Updates job progress and logs for the frontend polling."""
    if job_id not in JOBS:
        JOBS[job_id] = {
            "id": job_id,
            "stage": stage,
            "progress": progress,
            "message": message,
            "logs": [],
            "error": None,
            "completed": False,
            "video_url": None,
            "metadata": {}
        }
    
    j = JOBS[job_id]
    j["stage"] = stage
    j["progress"] = progress
    j["message"] = message
    timestamp = time.strftime("%H:%M:%S")
    j["logs"].append(f"[{timestamp}] {message}")
    if data:
        j["metadata"].update(data)

def run_full_pipeline(
    prompt: str,
    job_id: str,
    scene_count: int = 4,
    aspect_ratio: str = "16:9",
    style: str = "cinematic",
    voice_id: str = "en-US-ChristopherNeural",
    add_music: bool = True,
    subtitle_color: str = "yellow",
    api_key: str = None,
    image_api_key: str = None
):
    """Executes the entire end-to-end prompt to video pipeline."""
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    try:
        # Step 1: Generate Script
        update_job_status(job_id, "scripting", 10, f"Writing cinematic script for '{prompt}'...")
        script_data = generate_script(
            prompt=prompt,
            scene_count=scene_count,
            style=style,
            api_key=api_key
        )
        title = script_data.get("title", prompt.capitalize())
        scenes = script_data.get("scenes", [])
        if not scenes:
            raise ValueError("No scenes could be generated for this prompt")

        update_job_status(
            job_id,
            "scripting",
            25,
            f"Story created: '{title}' with {len(scenes)} scenes.",
            {"title": title, "scenes": scenes}
        )

        scene_clips = []
        total_duration = 0.0
        processed_scenes = []

        # Step 2 & 3: Generate Voiceover, Subtitles, and Visuals for each scene
        for idx, scene in enumerate(scenes):
            s_num = idx + 1
            narr = scene.get("narration", "")
            vis_prompt = scene.get("visual_prompt", prompt)
            sub_text = scene.get("subtitle_text", narr)

            # 2a. Voiceover
            update_job_status(
                job_id,
                "voiceover",
                25 + int((idx / len(scenes)) * 25),
                f"Synthesizing neural voiceover for Scene {s_num}/{len(scenes)}..."
            )
            audio_file = os.path.join(job_dir, f"scene_{idx}.mp3")
            duration = generate_scene_audio(narr, voice_id, audio_file)
            total_duration += duration

            # 2b. Subtitles
            srt_file = os.path.join(job_dir, f"scene_{idx}.srt")
            generate_scene_srt(sub_text, duration, srt_file)

            # 3. Image Generation
            update_job_status(
                job_id,
                "visuals",
                50 + int((idx / len(scenes)) * 25),
                f"Generating visuals for Scene {s_num}/{len(scenes)}: '{vis_prompt[:40]}...'..."
            )
            img_file = os.path.join(job_dir, f"scene_{idx}.jpg")
            generate_scene_image(
                prompt=vis_prompt,
                aspect_ratio=aspect_ratio,
                style=style,
                output_path=img_file,
                seed=42 + idx * 7,
                image_api_key=image_api_key,
                api_key=api_key
            )

            # 4. Render Scene Video Clip
            update_job_status(
                job_id,
                "rendering",
                75 + int((idx / len(scenes)) * 15),
                f"Rendering Scene {s_num}/{len(scenes)} with camera motion and subtitles..."
            )
            clip_file = os.path.join(job_dir, f"clip_{idx}.mp4")
            render_success = render_scene_clip(
                image_path=img_file,
                audio_path=audio_file,
                srt_path=srt_file,
                output_path=clip_file,
                duration=duration,
                aspect_ratio=aspect_ratio,
                scene_idx=idx,
                subtitle_color=subtitle_color
            )
            if render_success and os.path.exists(clip_file):
                scene_clips.append(clip_file)

            processed_scenes.append({
                "scene_id": s_num,
                "narration": narr,
                "visual_prompt": vis_prompt,
                "duration": round(duration, 2),
                "image_file": f"/temp/{job_id}/scene_{idx}.jpg",
                "audio_file": f"/temp/{job_id}/scene_{idx}.mp3"
            })

        # Step 5: Stitch into Final Video
        update_job_status(job_id, "assembly", 92, "Assembling final video with audio sync & ambient score...")
        final_video_name = f"{job_id}.mp4"
        final_output_path = os.path.join(OUTPUT_DIR, final_video_name)

        assemble_full_video(
            scene_clips=scene_clips,
            output_video_path=final_output_path,
            total_duration=total_duration,
            add_music=add_music,
            job_dir=job_dir
        )

        if not os.path.exists(final_output_path):
            raise RuntimeError("Final video assembly produced no output file")

        # Save metadata
        meta_path = os.path.join(OUTPUT_DIR, f"{job_id}.json")
        meta_data = {
            "job_id": job_id,
            "title": title,
            "prompt": prompt,
            "duration": round(total_duration, 1),
            "aspect_ratio": aspect_ratio,
            "style": style,
            "voice_id": voice_id,
            "scenes": processed_scenes,
            "video_url": f"/output/{final_video_name}",
            "created_at": time.time()
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2)

        j = JOBS[job_id]
        j["completed"] = True
        j["progress"] = 100
        j["stage"] = "done"
        j["message"] = "Video generation complete! Enjoy your video."
        j["video_url"] = f"/output/{final_video_name}"
        j["metadata"] = meta_data
        j["logs"].append(f"[{time.strftime('%H:%M:%S')}] Render complete: {final_video_name} ({round(total_duration, 1)}s)")

    except Exception as e:
        logger.exception("Pipeline execution failed")
        if job_id in JOBS:
            j = JOBS[job_id]
            j["completed"] = True
            j["error"] = str(e)
            j["stage"] = "error"
            j["message"] = f"Failed: {str(e)}"
            j["logs"].append(f"[{time.strftime('%H:%M:%S')}] ERROR: {str(e)}")

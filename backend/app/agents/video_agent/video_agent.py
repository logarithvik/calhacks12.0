"""
Video Generator Agent - Creates educational videos from clinical trial information

This agent integrates the full agentic workflow:
1. Stage 1: Generate video script and segment planning
2. Stage 2: Extract visual asset requirements
3. Stage 3: Generate images using Pollinations AI
4. Stage 4: Remove backgrounds from images
5. Stage 5: Plan slide layouts
6. Stage 6: Create professional slides with ffmpeg
7. Stage 7: Compose final video with narration and music

All intermediate outputs are stored in organized directories.
"""

import os
import json
import logging
import shutil
from typing import Dict, Any, Optional
from datetime import datetime

# Import all the workflow stages from agent.py
from .agent import (
    stage1_generate_script,
    stage2_generate_assets,
    stage3_generate_images,
    stage4_remove_backgrounds,
    stage5_generate_slides,
    stage6_create_ffmpeg_slides,
    stage7_compose_video,
    save_json,
    load_text_file
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def run_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the complete video generation pipeline.
    
    Args:
        input_data: Dictionary containing:
            - trial_data: Structured trial information from distill agent
            - simple_text: Patient-friendly summary text
            - trial_id: ID of the trial
            - duration: Target video duration in seconds (optional, default 90)
            - music_path: Optional path to background music file
    
    Returns:
        Dictionary containing:
            - file_path: Path to the final video file
            - status: "success" or "error"
            - intermediate_outputs: Paths to all intermediate files
            - metadata: Video metadata (duration, resolution, etc.)
    """
    
    trial_id = input_data.get("trial_id")
    trial_data = input_data.get("trial_data", {})
    simple_text = input_data.get("simple_text", "")
    target_duration = input_data.get("duration", 90)
    music_path = input_data.get("music_path")
    
    # Set up organized output directories for this specific trial
    base_dir = os.path.join("uploads", "video_outputs", f"trial_{trial_id}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trial_output_dir = os.path.join(base_dir, timestamp)
    
    # Create organized subdirectories
    dirs = {
        "outputs": os.path.join(trial_output_dir, "outputs"),
        "images": os.path.join(trial_output_dir, "images"),
        "images_nobg": os.path.join(trial_output_dir, "images", "no_bg"),
        "slides": os.path.join(trial_output_dir, "slides"),
        "prompts": os.path.join(trial_output_dir, "prompts")
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    logging.info(f"Starting video generation pipeline for trial {trial_id}")
    logging.info(f"Output directory: {trial_output_dir}")
    
    try:
        # Prepare trial summary text (combine structured data and simple text)
        trial_summary = f"""
Clinical Trial Summary:

{simple_text}

Structured Information:
{json.dumps(trial_data, indent=2)}
"""
        
        # Save input summary for reference
        summary_path = os.path.join(dirs["outputs"], "input_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(trial_summary)
        
        # Stage 1: Generate video script and segment planning
        logging.info("Stage 1: Generating video script and segments...")
        script_path = os.path.join(dirs["outputs"], "step1_script.json")
        script_data = stage1_generate_script(
            trial_summary=trial_summary,
            out_path=script_path
        )
        logging.info(f"✓ Script generated: {len(script_data.get('segments', []))} segments")
        
        # Stage 2: Generate visual asset requirements
        logging.info("Stage 2: Extracting visual asset requirements...")
        assets_path = os.path.join(dirs["outputs"], "step2_assets.json")
        
        # Copy prompt files to trial directory for reference
        agent_dir = os.path.dirname(__file__)
        prompt_files = [
            "video_transcript_generation_prompt.txt",
            "video_asset_generation_prompt.txt",
            "video_prompt_prompts.txt",
            "canvaa_prompts.txt"
        ]
        for pfile in prompt_files:
            src = os.path.join(agent_dir, pfile)
            if os.path.exists(src):
                shutil.copy(src, dirs["prompts"])
        
        # Temporarily update prompt paths for this trial
        original_prompts_dir = os.path.join(agent_dir, "example")
        temp_prompts_dir = dirs["prompts"]
        
        # Update the module's prompt paths temporarily
        import app.agents.video_agent.agent as agent_module
        original_prompt_assets = agent_module.PROMPT_ASSETS
        agent_module.PROMPT_ASSETS = os.path.join(agent_dir, "video_asset_generation_prompt.txt")
        
        try:
            assets_data = stage2_generate_assets(
                step1_path=script_path,
                out_path=assets_path
            )
            logging.info(f"✓ Assets defined: {len(assets_data)} visual elements")
        finally:
            # Restore original paths
            agent_module.PROMPT_ASSETS = original_prompt_assets
        
        # Stage 3: Generate images using Pollinations AI
        logging.info("Stage 3: Generating images with AI...")
        images_data = stage3_generate_images(
            step2_path=assets_path,
            images_dir=dirs["images"]
        )
        logging.info(f"✓ Images generated: {len(images_data)} images")
        
        # Stage 4: Remove backgrounds from images
        logging.info("Stage 4: Removing image backgrounds...")
        images_nobg = stage4_remove_backgrounds(
            images_info=images_data,
            output_dir=dirs["images"]
        )
        logging.info(f"✓ Backgrounds removed: {sum(1 for i in images_nobg if i.get('background_removed'))} images")
        
        # Stage 5: Plan slide layouts
        logging.info("Stage 5: Planning slide layouts...")
        slides_json_path = os.path.join(dirs["outputs"], "step4_slides.json")
        
        # Update prompt path for canva stage
        agent_module.PROMPT_CANVA = os.path.join(agent_dir, "canvaa_prompts.txt")
        
        slides_data = stage5_generate_slides(
            step1_path=script_path,
            step2_path=assets_path,
            images_info=images_nobg,
            out_path=slides_json_path
        )
        logging.info(f"✓ Slide layouts planned: {len(slides_data)} slides")
        
        # Stage 6: Create professional slides with ffmpeg
        logging.info("Stage 6: Creating professional slides...")
        slide_info = stage6_create_ffmpeg_slides(
            slides_json_path=slides_json_path,
            images_info=images_nobg,
            output_dir=dirs["slides"]
        )
        logging.info(f"✓ Slides created: {len(slide_info)} slide images")
        
        # Stage 7: Compose final video
        logging.info("Stage 7: Composing final video...")
        final_video_path = os.path.join(trial_output_dir, "final_video.mp4")
        video_path = stage7_compose_video(
            slides_path=slides_json_path,
            step1_path=script_path,
            slides_dir=dirs["slides"],
            output_video=final_video_path,
            music_path=music_path,
            use_canva_slides=True
        )
        logging.info(f"✓ Video composed: {video_path}")
        
        # Create metadata file
        metadata = {
            "trial_id": trial_id,
            "generated_at": timestamp,
            "video_path": video_path,
            "duration_target": target_duration,
            "segments_count": len(script_data.get('segments', [])),
            "assets_count": len(assets_data),
            "images_count": len(images_data),
            "slides_count": len(slide_info),
            "status": "success"
        }
        
        metadata_path = os.path.join(trial_output_dir, "metadata.json")
        save_json(metadata, metadata_path)
        
        # Return comprehensive result
        return {
            "file_path": video_path,
            "status": "success",
            "metadata": metadata,
            "intermediate_outputs": {
                "script": script_path,
                "assets": assets_path,
                "images": dirs["images"],
                "slides": dirs["slides"],
                "metadata": metadata_path
            }
        }
    
    except Exception as e:
        logging.error(f"Video generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Save error information
        error_info = {
            "trial_id": trial_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": timestamp,
            "status": "error"
        }
        
        error_path = os.path.join(trial_output_dir, "error.json")
        save_json(error_info, error_path)
        
        return {
            "file_path": None,
            "status": "error",
            "error": str(e),
            "error_details": error_path
        }
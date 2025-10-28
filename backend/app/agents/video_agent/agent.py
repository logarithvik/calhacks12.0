"""agent.py

End-to-end workflow to turn clinical-trial summaries into short patient-friendly
educational videos. Stages are modular and can be run independently.

Stages implemented:
  1) Video Script & Segment Planning (Gemini -> step1_script.json)
  2) Visual Asset Extraction (Gemini -> step2_assets.json)
  3) Image Generation (Pollinations -> images/)
  4) Background Removal (rembg -> images/no_bg/)
  5) Slide Layout Planning (Gemini -> step4_slides.json)
  6) Slide Creation (ffmpeg + PIL -> pptx_slides/)
  7) Video Composition (ffmpeg + TTS -> final_video.mp4)

Configuration and API keys are read from environment variables.
"""

import os
import re
import io
import json
import time
import shutil
import logging
import tempfile
import subprocess
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Optional background removal library
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except Exception:
    REMBG_AVAILABLE = False
    logging.warning("rembg not available - background removal will be skipped. Install with: pip install rembg")

# Optional local TTS fallback
try:
    import pyttsx3
    TTS_LOCAL_AVAILABLE = True
except Exception:
    TTS_LOCAL_AVAILABLE = False

# Basic logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


### -------------------- Configuration --------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Model choice and params
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))

# Slide settings (for ffmpeg-based slide creation)
SLIDE_WIDTH = 1920  # pixels (Full HD)
SLIDE_HEIGHT = 1080  # pixels (16:9 aspect ratio)

# File paths for prompts (relative to repo) 
PROMPTS_DIR = os.path.join("app/agents/video_agent/")
PROMPT_TRANSCRIPT = os.path.join(PROMPTS_DIR, "video_transcript_generation_prompt.txt")
PROMPT_ASSETS = os.path.join(PROMPTS_DIR, "video_asset_generation_prompt.txt")
PROMPT_IMAGE_PROMPTS = os.path.join(PROMPTS_DIR, "video_prompt_prompts.txt")
PROMPT_CANVA = os.path.join(PROMPTS_DIR, "canvaa_prompts.txt")

# Output paths
OUT_DIR = os.path.join("outputs")
IMAGES_DIR = os.path.join("images")
PPTX_SLIDES_DIR = os.path.join("pptx_slides")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(PPTX_SLIDES_DIR, exist_ok=True)

# Pollinations quick image endpoint
POLLINATIONS_IMG_ENDPOINT = "https://image.pollinations.ai/prompt/"


### -------------------- Gemini Setup --------------------
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment (.env) — required")

genai.configure(api_key=GEMINI_API_KEY)
GENIE_MODEL = genai.GenerativeModel(GEMINI_MODEL_NAME)


### -------------------- Utility helpers --------------------
def load_text_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def save_json(obj: Any, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    logging.info("Wrote %s", path)


def robust_parse_json(text: str) -> Any:
    """Try to find and parse the first JSON object in text.

    Gems: models sometimes return text with prose + JSON. We extract the JSON part.
    """
    # Attempt direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Regex to find {...} or [ ... ] blocks
    m = re.search(r"(\{(?:.|\n)*\}|\[(?:.|\n)*\])", text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # Last resort: try to fix common issues
    cleaned = text.strip().split("\n")
    joined = "".join(line for line in cleaned if line.strip())
    try:
        return json.loads(joined)
    except Exception:
        raise ValueError("Unable to parse JSON from model output")


def call_gemini(prompt: str, system: Optional[str] = None, temperature: float = GEMINI_TEMPERATURE) -> str:
    """Send a prompt to Gemini and return the text output. Keeps usage consistent with original file.

    Uses `GENIE_MODEL.generate_content(prompt)` as the prior code did.
    """
    full_prompt = (system + "\n\n" + prompt) if system else prompt
    logging.info("Calling Gemini model %s (temp=%s)...", GEMINI_MODEL_NAME, temperature)
    try:
        res = GENIE_MODEL.generate_content(full_prompt)
        text = res.text if getattr(res, "text", None) else str(res)
        return text
    except Exception as e:
        logging.error("Gemini call failed: %s", e)
        raise


### -------------------- Validation helpers --------------------
def validate_script_json(obj: Dict[str, Any]) -> bool:
    """Validate step1 video transcript JSON against the expected structure.
    
    Based on the sample output in example/video_transcript_generation_prompt.txt:
    - Must have: video_title (str), video_intro (str), segments (list)
    - Each segment must have: section_title, narration, image_description, educational_goal
    - video_title should be short and descriptive
    - video_intro should be 1-2 friendly sentences
    - Each section_title should be 3-6 words
    - narration should be conversational and clear (8th-grade level)
    - image_description should describe simple, cartoon-like visuals
    """
    # Check top-level required fields
    required_top = ["video_title", "video_intro", "segments"]
    for k in required_top:
        if k not in obj:
            logging.error("step1 missing required key: %s", k)
            return False
    
    # Validate video_title
    if not isinstance(obj["video_title"], str) or len(obj["video_title"].strip()) == 0:
        logging.error("step1 'video_title' must be a non-empty string")
        return False
    
    # Validate video_intro
    if not isinstance(obj["video_intro"], str) or len(obj["video_intro"].strip()) == 0:
        logging.error("step1 'video_intro' must be a non-empty string")
        return False
    
    # Validate segments
    if not isinstance(obj["segments"], list) or len(obj["segments"]) == 0:
        logging.error("step1 'segments' must be a non-empty list (expected 2-3 segments)")
        return False
    
    # Validate each segment structure
    required_segment_fields = ["section_title", "narration", "image_description", "educational_goal"]
    for idx, seg in enumerate(obj["segments"]):
        if not isinstance(seg, dict):
            logging.error("segment %d must be a dictionary", idx)
            return False
        
        for field in required_segment_fields:
            if field not in seg:
                logging.error("segment %d missing required field: %s", idx, field)
                return False
            
            if not isinstance(seg[field], str) or len(seg[field].strip()) == 0:
                logging.error("segment %d field '%s' must be a non-empty string", idx, field)
                return False
        
        # Additional validation: section_title should be relatively short (3-6 words guideline)
        title_word_count = len(seg["section_title"].split())
        if title_word_count > 10:
            logging.warning("segment %d 'section_title' has %d words (guideline is 3-6 words)", idx, title_word_count)
    
    logging.info("step1 JSON validation passed (%d segments)", len(obj["segments"]))
    return True


def validate_assets_json(obj: List[Dict[str, Any]]) -> bool:
    if not isinstance(obj, list):
        logging.error("assets JSON must be a list")
        return False
    for a in obj:
        for k in ["name", "style", "purpose", "prompt"]:
            if k not in a:
                logging.error("asset missing %s", k)
                return False
    return True


### -------------------- Stage implementations --------------------
def simplify_image_prompt(original_prompt: str) -> str:
    """Use Gemini to simplify an image generation prompt that failed.
    
    Applies clear guidelines to make the prompt more likely to succeed:
    - Remove complex details
    - Use simpler language
    - Focus on core visual elements
    - Keep it short and concrete
    """
    simplification_system_prompt = """You are an expert at creating simple, effective image generation prompts.

Your task: simplify the given image prompt to make it more likely to succeed with AI image generators.

Guidelines for simplification:
1. Remove unnecessary details and complexity
2. Use simple, concrete visual language
3. Focus on the core subject and style
4. Keep the prompt under 15 words
5. Use basic colors, shapes, and compositions
6. Avoid abstract concepts or complex scenes
7. Maintain the educational purpose but simplify execution

Output ONLY the simplified prompt text - no explanations, no extra commentary."""

    full_prompt = f"{simplification_system_prompt}\n\nOriginal prompt: {original_prompt}\n\nSimplified prompt:"
    
    try:
        simplified = call_gemini(full_prompt, temperature=0.3)
        # Clean up the response
        simplified = simplified.strip().strip('"\'')
        logging.info("Simplified prompt: '%s' -> '%s'", original_prompt[:50], simplified[:50])
        return simplified
    except Exception as e:
        logging.error("Failed to simplify prompt with Gemini: %s", e)
        # Fallback: create a very basic simplified version
        words = original_prompt.split()[:8]  # Take first 8 words
        return " ".join(words)



def stage1_generate_script(trial_summary: str, out_path: str = os.path.join(OUT_DIR, "step1_script.json")) -> Dict[str, Any]:
    """Use Gemini with `video_transcript_generation_prompt.txt` to create the script JSON.

    Inputs: trial_summary (string)
    Outputs: step1_script.json saved to out_path
    """
    prompt_template = load_text_file(PROMPT_TRANSCRIPT)
    prompt = prompt_template + "\n\nClinical Trial Summary:\n" + trial_summary + "\n\nRespond with a JSON object containing video_title, video_intro, and segments as described."

    raw = call_gemini(prompt, system=None)
    try:
        parsed = robust_parse_json(raw)
    except Exception as e:
        logging.error("Failed to parse Gemini output for stage1: %s", e)
        raise

    if not isinstance(parsed, dict) or not validate_script_json(parsed):
        raise ValueError("Invalid step1 JSON structure")

    save_json(parsed, out_path)
    return parsed


def stage2_generate_assets(step1_path: str = os.path.join(OUT_DIR, "step1_script.json"), out_path: str = os.path.join(OUT_DIR, "step2_assets.json")) -> List[Dict[str, Any]]:
    """For each segment image_description, ask Gemini to produce visual assets (name, style, purpose, prompt).

    Output: step2_assets.json (list of assets per segment)
    """
    with open(step1_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    all_assets = []
    prompt_template = load_text_file(PROMPT_ASSETS)
    
    # Include full script context from stage 1
    context_prompt = f"""Previous Stage Output (Video Script):
{json.dumps(script, indent=2, ensure_ascii=False)}

Use this complete video script as context when generating visual assets.
"""

    for idx, seg in enumerate(script["segments"]):
        image_desc = seg.get("image_description", "")
        prompt = context_prompt + "\n\n" + prompt_template + "\n\nImage description:\n" + image_desc + "\n\nReturn a JSON list of assets with fields: name, style, purpose, prompt. Keep items short and simple."
        raw = call_gemini(prompt)
        parsed = robust_parse_json(raw)

        # Save intermediate output for debugging before validation
        debug_path = os.path.join(OUT_DIR, f"step2_segment{idx}_raw.json")
        save_json({"segment_index": idx, "raw_response": raw, "parsed_response": parsed}, debug_path)
        
        # Extract assets from nested structure if needed
        # Gemini sometimes returns {"segments": [{"visual_assets": [...]}]} instead of a flat list
        assets = parsed
        if isinstance(parsed, dict):
            # Check for nested structure patterns
            if "segments" in parsed and isinstance(parsed["segments"], list) and len(parsed["segments"]) > 0:
                if "visual_assets" in parsed["segments"][0]:
                    assets = parsed["segments"][0]["visual_assets"]
                    logging.info("Extracted assets from nested 'segments[0].visual_assets' structure")
            elif "visual_assets" in parsed:
                assets = parsed["visual_assets"]
                logging.info("Extracted assets from 'visual_assets' key")
            elif "assets" in parsed:
                assets = parsed["assets"]
                logging.info("Extracted assets from 'assets' key")
        
        if not validate_assets_json(assets):
            logging.error("Asset generation validation failed for segment %s. Structure: %s", idx, type(assets))
            raise ValueError("Invalid assets JSON")
        # attach segment index for provenance
        for a in assets:
            a.setdefault("segment_index", idx)
        all_assets.extend(assets)

    save_json(all_assets, out_path)
    return all_assets




def stage3_generate_images(step2_path: str = os.path.join(OUT_DIR, "step2_assets.json"), images_dir: str = IMAGES_DIR) -> List[Dict[str, Any]]:
    """Generate images using Pollinations (simple GET endpoint). Save images/<asset_name>.png
    
    Includes retry logic with Gemini-based prompt simplification:
    - Tries original prompt 3 times
    - If all fail, simplifies prompt using Gemini
    - Tries simplified prompt 3 more times
    - Logs failures but continues processing other images

    Returns list of {name, path, prompt}
    """
    with open(step2_path, "r", encoding="utf-8") as f:
        assets = json.load(f)

    results = []
    for item in assets:
        name = re.sub(r"[^A-Za-z0-9_-]", "_", item.get("name", "asset"))
        original_prompt = item.get("prompt") or item.get("name")
        
        # Try with original prompt first (3 attempts)
        success = False
        img_path = os.path.join(images_dir, f"{name}.png")
        current_prompt = original_prompt
        
        for attempt in range(1, 4):  # 3 attempts with original prompt
            url = POLLINATIONS_IMG_ENDPOINT + requests.utils.quote(current_prompt)
            logging.info("Requesting image for '%s' (attempt %d/3)", name, attempt)
            try:
                r = requests.get(url, timeout=60)
                r.raise_for_status()
                
                # Verify we got actual image data (not error HTML)
                if len(r.content) < 1000:
                    raise ValueError("Response too small to be a valid image")
                
                with open(img_path, "wb") as fh:
                    fh.write(r.content)
                results.append({"name": name, "path": img_path, "prompt": current_prompt})
                logging.info("✓ Saved image %s", img_path)
                success = True
                break
            except Exception as e:
                logging.warning("Attempt %d failed for '%s': %s", attempt, name, e)
                time.sleep(1)  # Brief pause before retry
        
        # If original prompt failed 3 times, simplify and try again
        if not success:
            logging.info("Original prompt failed 3 times. Simplifying prompt with Gemini...")
            simplified_prompt = simplify_image_prompt(original_prompt)
            current_prompt = simplified_prompt
            
            for attempt in range(1, 4):  # 3 attempts with simplified prompt
                url = POLLINATIONS_IMG_ENDPOINT + requests.utils.quote(current_prompt)
                logging.info("Requesting image for '%s' with simplified prompt (attempt %d/3)", name, attempt)
                try:
                    r = requests.get(url, timeout=60)
                    r.raise_for_status()
                    
                    if len(r.content) < 1000:
                        raise ValueError("Response too small to be a valid image")
                    
                    with open(img_path, "wb") as fh:
                        fh.write(r.content)
                    results.append({"name": name, "path": img_path, "prompt": current_prompt, "simplified": True})
                    logging.info("✓ Saved image %s with simplified prompt", img_path)
                    success = True
                    break
                except Exception as e:
                    logging.warning("Simplified attempt %d failed for '%s': %s", attempt, name, e)
                    time.sleep(1)
        
        if not success:
            logging.error("✗ Failed to generate image for '%s' after 6 total attempts (3 original + 3 simplified)", name)
        else:
            time.sleep(0.5)  # Rate limiting between successful requests

    return results


def stage4_remove_backgrounds(images_info: List[Dict[str, Any]], output_dir: str = IMAGES_DIR) -> List[Dict[str, Any]]:
    """Remove backgrounds from generated images to create true transparent PNGs.
    
    Uses the rembg library to automatically remove backgrounds. If rembg is not available,
    this stage is skipped and original images are used.
    
    Input: List of image info dicts from stage3 with 'path' field
    Output: List of image info dicts with updated 'path' pointing to background-removed versions
    """
    if not REMBG_AVAILABLE:
        logging.warning("Skipping background removal - rembg not installed. Images will keep their backgrounds.")
        return images_info
    
    results = []
    processed_dir = os.path.join(output_dir, "no_bg")
    os.makedirs(processed_dir, exist_ok=True)
    
    for idx, img_info in enumerate(images_info):
        original_path = img_info.get("path")
        if not original_path or not os.path.exists(original_path):
            logging.warning("Skipping background removal for missing image: %s", original_path)
            results.append(img_info)
            continue
        
        name = img_info.get("name", f"image_{idx}")
        output_path = os.path.join(processed_dir, f"{name}_nobg.png")
        
        logging.info("Removing background from '%s'...", name)
        try:
            # Load the image
            with open(original_path, 'rb') as input_file:
                input_data = input_file.read()
            
            # Remove background
            output_data = remove(input_data)
            
            # Save as PNG with transparency
            with open(output_path, 'wb') as output_file:
                output_file.write(output_data)
            
            # Update the image info with new path
            updated_info = img_info.copy()
            updated_info['path'] = output_path
            updated_info['original_path'] = original_path
            updated_info['background_removed'] = True
            results.append(updated_info)
            
            logging.info("✓ Saved background-removed image: %s", output_path)
            
        except Exception as e:
            logging.error("Failed to remove background from '%s': %s - using original", name, e)
            # Keep original image on failure
            results.append(img_info)
    
    logging.info("Background removal complete: %d/%d images processed successfully", 
                 sum(1 for r in results if r.get('background_removed')), len(images_info))
    return results


def stage5_generate_slides(step1_path: str = os.path.join(OUT_DIR, "step1_script.json"), 
                           step2_path: str = os.path.join(OUT_DIR, "step2_assets.json"),
                           images_info: List[Dict[str, Any]] = None, 
                           out_path: str = os.path.join(OUT_DIR, "step4_slides.json")) -> List[Dict[str, Any]]:
    """Use Gemini + `canvaa_prompts.txt` to generate slide layout JSON.
    
    Now includes context from all previous stages (script, assets, generated images).

    Output: step4_slides.json with slide_title, images (positions/sizes/layers), caption, caption_position, slide_duration
    """
    with open(step1_path, "r", encoding="utf-8") as f:
        script = json.load(f)
    
    # Load stage 2 assets for context
    assets = []
    if os.path.exists(step2_path):
        with open(step2_path, "r", encoding="utf-8") as f:
            assets = json.load(f)

    image_index = {os.path.splitext(os.path.basename(i["path"]))[0]: i for i in (images_info or [])}
    prompt_template = load_text_file(PROMPT_CANVA)
    
    # Build comprehensive context from all previous stages
    context_prompt = f"""Previous Stage Outputs:

STAGE 1 - Video Script:
{json.dumps(script, indent=2, ensure_ascii=False)}

STAGE 2 - Visual Assets Plan:
{json.dumps(assets, indent=2, ensure_ascii=False)}

STAGE 3/4 - Generated Images (available for use):
{json.dumps(list(image_index.keys()), indent=2, ensure_ascii=False)}

Use all of the above context when designing slide layouts to ensure consistency with the overall video narrative and available visual assets.
"""

    slides = []
    for idx, seg in enumerate(script["segments"]):
        prompt = context_prompt + "\n\n" + prompt_template + "\n\nSegment:\n" + json.dumps(seg, ensure_ascii=False)
        # Provide available images for this segment
        candidate_images = [n for n,p in image_index.items() if str(idx) in (p.get("path") or "") or True]
        prompt += "\n\nAvailable images: " + ", ".join(candidate_images)
        raw = call_gemini(prompt)
        parsed = robust_parse_json(raw)
        # Expect parsed to be a dict describing a slide
        slide = parsed if isinstance(parsed, dict) else {"slide_title": seg.get("section_title"), "caption": seg.get("educational_goal"), "slide_duration": 6, "images": []}
        slide.setdefault("slide_title", seg.get("section_title"))
        slide.setdefault("caption", seg.get("educational_goal"))
        slide.setdefault("slide_duration", max(5, min(12, len(seg.get("narration", "").split()) // 2)))
        slides.append(slide)

    save_json(slides, out_path)
    return slides


def tts_synthesize(text: str, out_path: str, voice: str = "alloy", cheerful: bool = True) -> str:
    """Create an audio file for the narration. Prefer ElevenLabs if key provided; otherwise fallback to local pyttsx3 if available.

    Returns path to audio file (wav)
    Raises RuntimeError if no TTS service is available.
    """
    if ELEVENLABS_API_KEY:
        # Minimal ElevenLabs example using their text-to-speech API
        url = "https://api.elevenlabs.io/v1/text-to-speech/" + voice
        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        body = {"text": text, "voice_settings": {"stability":0.6, "similarity_boost":0.6}}
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(resp.content)
            return out_path
        except Exception as e:
            logging.error("ElevenLabs TTS failed: %s", e)
            raise RuntimeError(f"ElevenLabs TTS failed: {str(e)}")

    if TTS_LOCAL_AVAILABLE:
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.save_to_file(text, out_path)
            engine.runAndWait()
            return out_path
        except Exception as e:
            logging.error("Local TTS (pyttsx3) failed: %s", e)
            raise RuntimeError(f"Local TTS failed: {str(e)}")

    raise RuntimeError("No TTS available: ELEVENLABS_API_KEY not configured and pyttsx3 not installed. Please provide ELEVENLABS_API_KEY in environment variables or install pyttsx3.")


def stage6_create_ffmpeg_slides(
    slides_json_path: str = os.path.join(OUT_DIR, "step4_slides.json"),
    images_info: List[Dict[str, Any]] = None,
    output_dir: str = PPTX_SLIDES_DIR
) -> List[Dict[str, Any]]:
    """Create slide images using ffmpeg by compositing images and text overlays.
    
    This approach uses ffmpeg's powerful filtering to:
    1. Create a dark background
    2. Overlay images at specified positions
    3. Add title and caption text with styling
    4. Export as PNG images
    
    Returns: List of exported slide info with paths to PNG files
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found - required for slide creation")
    
    with open(slides_json_path, "r", encoding="utf-8") as f:
        slides_data = json.load(f)
    
    # Build image lookup with fuzzy matching
    image_lookup = {}
    image_files_by_normalized = {}  # Normalized name -> full path mapping
    
    if images_info:
        for img in images_info:
            name = img.get("name", "")
            path = img.get("path", "")
            if not name or not path or not os.path.exists(path):
                continue
            
            # Create normalized version: lowercase, no underscores, no spaces, no _nobg
            normalized = name.lower().replace("_nobg", "").replace("_", "").replace(" ", "").replace("-", "")
            
            # Store with original name and variations
            image_lookup[name] = path
            image_lookup[name.lower()] = path
            image_files_by_normalized[normalized] = path
            
            # Also store without _nobg suffix
            if "_nobg" in name.lower():
                without_nobg = name.replace("_nobg", "").replace("_NOBG", "")
                image_lookup[without_nobg] = path
                image_lookup[without_nobg.lower()] = path
        
        logging.info("Built image lookup with %d entries from %d images", len(image_lookup), len(images_info))
    
    os.makedirs(output_dir, exist_ok=True)
    exported_slides = []
    
    # Slide dimensions (16:9 aspect ratio)
    slide_width = 1920
    slide_height = 1080
    
    for idx, slide_data in enumerate(slides_data):
        logging.info("Creating slide %d: %s", idx + 1, slide_data.get("slide_title", "Untitled"))
        
        output_path = os.path.join(output_dir, f"slide_{idx:03d}.png")
        
        try:
            # Start with a solid color background
            filter_parts = []
            inputs = []
            found_images = []  # Track actually found images
            
            # Add images from the slide
            for img_spec in slide_data['slides'][0].get("images", []):
                if isinstance(img_spec, dict):
                    img_name = img_spec.get("name")
                    position = img_spec.get("position", "center")
                    size_ratio = img_spec.get("size_ratio", 0.4)
                else:
                    img_name = img_spec
                    position = "center"
                    size_ratio = 0.4
                
                # Find image with aggressive fuzzy matching
                local_path = None
                
                # Try exact matches first (with various case combinations)
                for variant in [img_name, img_name.lower(), f"{img_name}_nobg", f"{img_name.lower()}_nobg"]:
                    if variant in image_lookup:
                        local_path = image_lookup[variant]
                        break
                
                # If not found, try normalized matching (remove spaces, underscores, case)
                if not local_path:
                    normalized_request = img_name.lower().replace("_", "").replace(" ", "").replace("-", "")
                    if normalized_request in image_files_by_normalized:
                        local_path = image_files_by_normalized[normalized_request]
                
                # If still not found, try partial matching (substring search)
                if not local_path:
                    normalized_request = img_name.lower().replace("_", "").replace(" ", "").replace("-", "")
                    for norm_name, path in image_files_by_normalized.items():
                        # Check if either name contains the other
                        if normalized_request in norm_name or norm_name in normalized_request:
                            local_path = path
                            logging.info("Fuzzy matched '%s' to '%s' via substring", img_name, os.path.basename(path))
                            break
                
                # If STILL not found, try word-based matching (split by common delimiters)
                if not local_path:
                    import re
                    # Extract words from the request
                    request_words = set(re.split(r'[_\s-]+', img_name.lower()))
                    request_words.discard('')
                    
                    best_match = None
                    best_score = 0
                    
                    for img_info in images_info:
                        available_name = img_info.get("name", "").lower().replace("_nobg", "")
                        available_words = set(re.split(r'[_\s-]+', available_name))
                        available_words.discard('')
                        
                        # Calculate match score (how many words overlap)
                        common_words = request_words & available_words
                        if len(common_words) > 0:
                            score = len(common_words) / max(len(request_words), len(available_words))
                            if score > best_score and score >= 0.5:  # At least 50% word overlap
                                best_score = score
                                best_match = img_info.get("path")
                    
                    if best_match:
                        local_path = best_match
                        logging.info("Fuzzy matched '%s' to '%s' via word matching (%.0f%% match)", 
                                   img_name, os.path.basename(local_path), best_score * 100)
                
                if not local_path:
                    logging.warning("Image '%s' not found, skipping", img_name)
                    continue
                
                # Calculate position and size
                img_width = int(slide_width * size_ratio)
                img_height = int(slide_height * size_ratio)
                x, y = _calculate_ffmpeg_position(position, slide_width, slide_height, img_width, img_height)
                
                # Store found image info
                found_images.append({
                    'path': local_path,
                    'name': img_name,
                    'position': position,
                    'width': img_width,
                    'height': img_height,
                    'x': x,
                    'y': y
                })
                logging.info("✓ Found image '%s' at position %s (%dx%d at %d,%d)", img_name, position, img_width, img_height, x, y)
            
            # Build ffmpeg command
            if len(found_images) == 0:
                # No images - just create a solid color background
                cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x2d3436:s={slide_width}x{slide_height}:d=1",
                       "-frames:v", "1", output_path]
            else:
                # Build filter_complex with found images
                # Start with background
                filter_parts.append(f"color=c=0x2d3436:s={slide_width}x{slide_height}:d=1[bg]")
                
                # Add each image as input and create scale filters
                for idx, img_info in enumerate(found_images):
                    inputs.extend(["-i", img_info['path']])
                    input_idx = idx + 1  # Input 0 is the color background, images start at 1
                    filter_parts.append(f"[{input_idx}:v]scale={img_info['width']}:{img_info['height']}[img{idx}]")
                
                # Build overlay chain
                overlay_chain = "[bg]"
                for idx, img_info in enumerate(found_images):
                    if idx < len(found_images) - 1:
                        # Not the last image - output to tmp
                        overlay_chain += f"[img{idx}]overlay={img_info['x']}:{img_info['y']}[tmp{idx}]"
                        overlay_chain += f"; [tmp{idx}]"
                    else:
                        # Last image - no need for tmp output
                        overlay_chain += f"[img{idx}]overlay={img_info['x']}:{img_info['y']}"
                
                filter_complex = "; ".join(filter_parts) + "; " + overlay_chain
                
                cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x2d3436:s={slide_width}x{slide_height}:d=1"]
                cmd.extend(inputs)
                cmd.extend(["-filter_complex", filter_complex, "-frames:v", "1", output_path])
            
            # Run ffmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error("ffmpeg failed: %s", result.stderr)
                raise RuntimeError(f"ffmpeg command failed: {result.stderr}")
            
            # Now add text overlays using PIL (more reliable than ffmpeg drawtext)
            if slide_data.get("slide_title") or slide_data.get("caption"):
                from PIL import Image, ImageDraw, ImageFont
                
                img = Image.open(output_path)
                draw = ImageDraw.Draw(img)
                
                # Try to load a nice font, fallback to default
                try:
                    title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 64)
                    caption_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)
                except:
                    try:
                        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
                        caption_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
                    except:
                        title_font = ImageFont.load_default()
                        caption_font = ImageFont.load_default()
                
                # Add title at top
                #print(slide_data)
                title = slide_data['slides'][0].get("slide_title", "")
                #print(title)
                if title:
                    # Get text bounding box for centering
                    bbox = draw.textbbox((0, 0), title, font=title_font)
                    text_width = bbox[2] - bbox[0]
                    text_x = (slide_width - text_width) // 2
                    text_y = 40
                    
                    # Draw text with shadow for better visibility
                    draw.text((text_x + 2, text_y + 2), title, fill=(0, 0, 0), font=title_font)  # Shadow
                    draw.text((text_x, text_y), title, fill=(255, 255, 255), font=title_font)  # Main text
                
                # Add caption at bottom with background
                caption = slide_data['slides'][0].get("caption", "")
                #print(caption)
                if caption:
                    # Calculate caption area
                    max_width = slide_width - 100
                    words = caption.split()
                    lines = []
                    current_line = []
                    
                    for word in words:
                        current_line.append(word)
                        test_line = " ".join(current_line)
                        bbox = draw.textbbox((0, 0), test_line, font=caption_font)
                        if bbox[2] - bbox[0] > max_width:
                            if len(current_line) > 1:
                                current_line.pop()
                                lines.append(" ".join(current_line))
                                current_line = [word]
                            else:
                                lines.append(test_line)
                                current_line = []
                    
                    if current_line:
                        lines.append(" ".join(current_line))
                    
                    # Draw semi-transparent background for caption
                    line_height = 50
                    caption_height = len(lines) * line_height + 40
                    caption_y = slide_height - caption_height - 30
                    
                    # Create semi-transparent overlay
                    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                    overlay_draw = ImageDraw.Draw(overlay)
                    overlay_draw.rectangle(
                        [(50, caption_y), (slide_width - 50, slide_height - 30)],
                        fill=(0, 0, 0, 180)
                    )
                    img = img.convert('RGBA')
                    img = Image.alpha_composite(img, overlay).convert('RGB')
                    draw = ImageDraw.Draw(img)
                    
                    # Draw caption text
                    for i, line in enumerate(lines):
                        bbox = draw.textbbox((0, 0), line, font=caption_font)
                        text_width = bbox[2] - bbox[0]
                        text_x = (slide_width - text_width) // 2
                        text_y = caption_y + 20 + i * line_height
                        draw.text((text_x, text_y), line, fill=(255, 255, 255), font=caption_font)
                
                # Save updated image
                img.save(output_path)
            
            exported_slides.append({
                "index": idx,
                "title": slide_data.get("slide_title"),
                "caption": slide_data.get("caption"),
                "path": output_path,
                "duration": slide_data.get("slide_duration", 6)
            })
            
            logging.info("✓ Created slide: %s", output_path)
            
        except Exception as e:
            logging.error("Failed to create slide %d: %s", idx, e)
            import traceback
            traceback.print_exc()
    
    # Save slide info
    info_path = os.path.join(OUT_DIR, "ffmpeg_slides_info.json")
    save_json(exported_slides, info_path)
    
    logging.info("Slide creation complete: %d/%d slides created", len(exported_slides), len(slides_data))
    return exported_slides


def _calculate_ffmpeg_position(position_str: str, canvas_width: int, canvas_height: int, 
                                element_width: int, element_height: int) -> tuple:
    """Calculate x,y coordinates for ffmpeg overlay filter based on position string.
    
    Returns: (x, y) as integers for ffmpeg overlay positioning
    """
    # Default to center
    x = (canvas_width - element_width) // 2
    y = (canvas_height - element_height) // 2
    
    position_lower = position_str.lower()
    
    # Horizontal positioning
    if "left" in position_lower:
        x = 50
    elif "right" in position_lower:
        x = canvas_width - element_width - 50
    
    # Vertical positioning
    if "top" in position_lower:
        y = 100
    elif "bottom" in position_lower:
        y = canvas_height - element_height - 100
    
    return (x, y)


def stage7_compose_video(slides_path: str = os.path.join(OUT_DIR, "step4_slides.json"),
                          step1_path: str = os.path.join(OUT_DIR, "step1_script.json"),
                          slides_dir: str = PPTX_SLIDES_DIR, 
                          output_video: str = os.path.join(OUT_DIR, "final_video.mp4"), 
                          music_path: Optional[str] = None, 
                          use_canva_slides: bool = True):
    """Assemble slides into an MP4 using ffmpeg. Creates narration per slide and composes.
    
    Now uses narration directly from Stage 1 script for more accurate voice-over.
    
    If use_canva_slides=True, uses professionally designed slides from python-pptx (stage 6).
    Otherwise, falls back to simple image+text composition with ffmpeg.

    This function requires ffmpeg to be installed and on PATH. If missing, it will raise.
    """
    # Check ffmpeg
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH — required for video composition")

    with open(slides_path, "r", encoding="utf-8") as f:
        slides = json.load(f)
    
    # Load Stage 1 script to get original narration
    script_segments = []
    if os.path.exists(step1_path):
        with open(step1_path, "r", encoding="utf-8") as f:
            script_data = json.load(f)
            script_segments = script_data.get("segments", [])
            logging.info("Loaded %d script segments from Stage 1 for narration", len(script_segments))
    else:
        logging.warning("Stage 1 script not found at %s - will use slide captions as fallback", step1_path)

    temp_dir = tempfile.mkdtemp(prefix="video_build_")
    logging.info("Using temp dir %s", temp_dir)
    segment_files = []

    # Generate per-slide media
    for i, slide in enumerate(slides):
        duration = slide.get("slide_duration", 6)
        
        # Use narration from Stage 1 script if available, otherwise fallback to slide data
        narration = ""
        if i < len(script_segments):
            narration = script_segments[i].get("narration", "")
            logging.info("Using Stage 1 narration for slide %d: '%s...'", i, narration[:50])
        
        # Fallback to slide data if no script narration available
        if not narration:
            narration = slide.get("narration") or slide.get("caption") or slide.get("slide_title", "")
            logging.warning("No Stage 1 narration for slide %d, using fallback", i)
        
        if isinstance(narration, list):
            narration = " ".join(narration)

        audio_path = os.path.join(temp_dir, f"slide_{i}.wav")
        try:
            tts_synthesize(narration, audio_path)
            logging.info("✓ Generated audio for slide %d", i)
            
        except RuntimeError as e:
            # TTS failed - this is a critical error, clean up and propagate
            logging.error("Audio generation failed for slide %d: %s", i, e)
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to generate audio for slide {i}: {str(e)}. Video creation cannot continue without audio narration.") from e
        except Exception as e:
            # Unexpected error
            logging.error("Unexpected error during TTS for slide %d: %s", i, e)
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Unexpected error generating audio for slide {i}: {str(e)}") from e

        try:
            audio_length_cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", audio_path
            ]
            audio_duration = float(subprocess.check_output(audio_length_cmd).decode().strip())
            duration = max(duration, audio_duration)
        except Exception as e:
            logging.warning("Could not determine audio duration for slide %s: %s", i, e)


        # Choose slide image
        img_entry = None
        
        if use_canva_slides:
            # Use Canva-generated slide (numbered slide_XXX.png)
            canva_slide = os.path.join(slides_dir, f"slide_{i:03d}.png")
            if os.path.exists(canva_slide):
                img_entry = canva_slide
                logging.info("Using Canva slide: %s", canva_slide)
        
        if not img_entry:
            # Fallback: use images from stage 3/4
            imgs = slide.get("images") or []
            if imgs:
                # support simple case where images is list of names
                img_name = imgs[0].get("name") if isinstance(imgs[0], dict) else imgs[0]
                # Check in Canva slides dir first, then fallback to IMAGES_DIR
                for search_dir in [slides_dir, IMAGES_DIR, os.path.join(IMAGES_DIR, "no_bg")]:
                    candidate = os.path.join(search_dir, f"{img_name}.png")
                    if os.path.exists(candidate):
                        img_entry = candidate
                        break

        if not img_entry:
            # pick any image in slides_dir or images_dir
            for search_dir in [slides_dir, IMAGES_DIR]:
                if os.path.exists(search_dir):
                    candidates = [os.path.join(search_dir, f) for f in os.listdir(search_dir) if f.lower().endswith(".png")]
                    if candidates:
                        img_entry = candidates[0]
                        break

        if not img_entry:
            logging.error("No images found for slide %s — skipping", i)
            continue

        # Make a video from image using simple zoompan (Ken Burns) via ffmpeg
        slide_video = os.path.join(temp_dir, f"slide_{i}.mp4")
        # Create a video with duration and a subtle zoom
        zoom_filter = "zoompan=z='if(lte(in,0),1,zoom+0.0008)':d=1"
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_entry, "-i", audio_path,
            "-vf", f"fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5",
            "-c:v", "libx264", "-t", str(duration), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            slide_video
        ]
        logging.info("Rendering slide video %s with audio", slide_video)
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error("ffmpeg failed for slide %d: %s", i, result.stderr)
        else:
            logging.info("✓ Slide %d video created with audio track", i)

        # Attach subtitle/caption as burned-in text can be done optionally; skip for simplicity.
        segment_files.append(slide_video)

    # Concatenate segment videos
    concat_list = os.path.join(temp_dir, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for sf in segment_files:
            f.write(f"file '{sf}'\n")

    final_tmp = os.path.join(temp_dir, "final_tmp.mp4")
    logging.info("Concatenating %d slide videos with audio...", len(segment_files))
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        final_tmp
    ]
    result = subprocess.run(concat_cmd, check=True, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("Video concatenation failed: %s", result.stderr)
        raise RuntimeError(f"Failed to concatenate videos: {result.stderr}")
    
    logging.info("✓ Video concatenation complete with audio")

    # Optionally add background music (looped softly)
    if music_path and os.path.exists(music_path):
        logging.info("Adding background music: %s", music_path)
        # Mix music at low volume
        music_cmd = [
            "ffmpeg", "-y", "-i", final_tmp, "-stream_loop", "-1", "-i", music_path,
            "-filter_complex", "[1:a]volume=0.15[a1];[0:a][a1]amix=inputs=2:duration=shortest[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            output_video
        ]
        subprocess.run(music_cmd, check=True)
        logging.info("✓ Background music added")
    else:
        shutil.move(final_tmp, output_video)
        logging.info("✓ Final video saved (no background music)")

    logging.info("Final video saved to %s", output_video)
    shutil.rmtree(temp_dir)
    return output_video


### -------------------- CLI / Orchestration --------------------
def run_full_pipeline(trial_summary: str, music_path: Optional[str] = None):
    # Stage 1
    script = stage1_generate_script(trial_summary)
    # Stage 2
    assets = stage2_generate_assets()
    # Stage 3 - Image Generation
    images = stage3_generate_images()
    # Stage 4 - Background Removal
    images_nobg = stage4_remove_backgrounds(images)
    # Stage 5 - Slide Layout Planning
    slides = stage5_generate_slides(images_info=images_nobg)
    # Stage 6 - Create Slides with ffmpeg
    try:
        canva_slides = stage6_create_ffmpeg_slides(images_info=images_nobg)
    except Exception as e:
        logging.warning("Slide creation failed: %s - will use fallback", e)
        canva_slides = []
    # Stage 7 - Video Composition
    try:
        video = stage7_compose_video(music_path=music_path, use_canva_slides=len(canva_slides) > 0)
        logging.info("Pipeline complete: %s", video)
    except Exception as e:
        logging.error("Video composition failed: %s", e)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a patient-friendly educational video from a clinical trial summary.")
    parser.add_argument("--summary", type=str, help="Path to a text file containing the clinical trial summary")
    parser.add_argument("--stage", type=int, choices=range(1,8), help="Run a specific stage (1-7). If omitted, runs full pipeline.")
    parser.add_argument("--music", type=str, help="Optional background music path (mp3/m4a) to mix into final video")
    args = parser.parse_args()

    if not args.summary:
        parser.error("--summary is required")

    with open(args.summary, "r", encoding="utf-8") as fh:
        summary_text = fh.read()

    # Minimal system prompt (keeps prior behavior of reading prompt.txt if present)
    if os.path.exists("prompt.txt"):
        system_prompt = load_text_file("prompt.txt")
    else:
        system_prompt = "You are an assistant that outputs JSON at 8th-grade reading level. Be concise, friendly and patient-focused."

    # Wire the system prompt into GEMINI calls by setting a simple wrapper (we already include system in call_gemini optionally)

    if args.stage:
        s = args.stage
        if s == 1:
            stage1_generate_script(summary_text)
        elif s == 2:
            stage2_generate_assets()
        elif s == 3:
            images = stage3_generate_images()
        elif s == 4:
            # For stage 4, need to load images from stage 3 output
            import glob
            image_files = glob.glob(os.path.join(IMAGES_DIR, "*.png"))
            images = [{"name": os.path.splitext(os.path.basename(f))[0], "path": f} for f in image_files]
            stage4_remove_backgrounds(images)
        elif s == 5:
            # For stage 5, need to load images with background removed
            import glob
            image_files = glob.glob(os.path.join(IMAGES_DIR, "no_bg", "*.png"))
            if not image_files:
                image_files = glob.glob(os.path.join(IMAGES_DIR, "*.png"))
            images = [{"name": os.path.splitext(os.path.basename(f))[0], "path": f} for f in image_files]
            stage5_generate_slides(images_info=images)
        elif s == 6:
            # For stage 6, need to load images with background removed
            import glob
            image_files = glob.glob(os.path.join(IMAGES_DIR, "no_bg", "*.png"))
            if not image_files:
                image_files = glob.glob(os.path.join(IMAGES_DIR, "*.png"))
            images = [{"name": os.path.splitext(os.path.basename(f))[0], "path": f} for f in image_files]
            slides_json_path = "outputs/step4_slides.json"  # or wherever your slide JSON is
            stage6_create_ffmpeg_slides(slides_json_path=slides_json_path, images_info=images)
        elif s == 7:
            stage7_compose_video(music_path=args.music)
    else:
        run_full_pipeline(summary_text, music_path=args.music)
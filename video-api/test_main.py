import os
import requests
import nltk
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
import json
import re

# compute output dirs
output_dir = os.path.join(os.path.dirname(__file__), "output")
mechanism_dir = os.path.join(output_dir, "mechanism_slides")
trial_dir = os.path.join(output_dir, "trial_slides")
for d in (output_dir, mechanism_dir, trial_dir):
    os.makedirs(d, exist_ok=True)

# Optional local TTS
try:
    import pyttsx3
except Exception:
    pyttsx3 = None

# Pollinations SDK (optional)
try:
    from pollinations import Image as PollImage
except Exception:
    PollImage = None

# Load environment
load_dotenv()
FISH_API_KEY = os.getenv("FISH_API_KEY")
USE_LOCAL_TTS = os.getenv("USE_LOCAL_TTS", "1") in ("1", "true", "True")

nltk.download("punkt", quiet=True)

class AIVideoAgent:
    def __init__(self, fish_key):
        self.fish_key = fish_key
        self.image_model = PollImage(width=1280, height=720, seed="random") if PollImage else None

    def is_mechanism_section(self, content: str, title: str) -> bool:
        """Determine if section describes biological/mechanism content."""
        mechanism_keywords = [
            "monoclonal antibody", "immune", "cells", "protein", 
            "receptor", "biological", "pathway", "targeting",
            "mechanism", "molecular", "antibody", "signaling",
            "purpose", "study mechanism", "how it works"
        ]
        return any(kw.lower() in content.lower() or kw.lower() in title.lower() 
                  for kw in mechanism_keywords)

    def generate_mechanism_image(self, content: str, index: int) -> str:
        """Generate image-only slide for biological mechanisms."""
        # Extract biological concepts for accurate representation
        bio_terms = re.findall(r'\b(?:antibody|receptor|protein|enzyme|cell|pathway|signaling|binding|complex)\w*\b', 
                             content.lower())
        
        amoeba_style = (
            "Create a biologically accurate mechanism illustration in Amoeba Sisters style. "
            "REQUIREMENTS: "
            "1. ABSOLUTELY NO TEXT OR LABELS - pure visual communication only. "
            "2. Use scientifically accurate shapes for: "
            "   - Antibody Y-shaped structures "
            "   - Precise receptor conformations "
            "   - Correct protein-protein interactions "
            "   - Accurate cellular compartments and membranes "
            "3. Style elements: "
            "   - Friendly rounded shapes and cheerful expressions "
            "   - Bright pastel colors for clarity "
            "   - Thick outlines for main structures "
            "   - Simple, uncluttered background "
            "4. Show process flow through: "
            "   - Clear directional movement "
            "   - Size relationships between components "
            "   - Interaction zones highlighted by color/shape "
            "5. Focus on mechanical accuracy while maintaining cute style"
        )

        mechanism_focus = (
            "Focus on precise biological representation of: " +
            ", ".join(bio_terms) if bio_terms else "the molecular mechanism"
        )

        full_prompt = f"Scientifically accurate {mechanism_focus}. {amoeba_style}"
        path = os.path.join(mechanism_dir, f"mechanism_{index}.png")
        
        try:
            if self.image_model:
                self.image_model(full_prompt, save=True, file=path)
            else:
                url = f"https://pollinations.ai/p/{requests.utils.quote(full_prompt)}?width=1280&height=720&nologo=true"
                r = requests.get(url, timeout=30)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content)).convert("RGB")
                    img.save(path)
            return path
        except Exception as e:
            print(f"Mechanism image generation failed: {e}")
            return self._create_fallback_slide(content, path)

    def generate_trial_slide(self, content: str, index: int) -> str:
        """Generate text-focused slide with statistics emphasis."""
        path = os.path.join(trial_dir, f"trial_{index}.png")
        w, h = 1280, 720
        img = Image.new("RGB", (w, h), (245, 245, 250))
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("arial.ttf", 36)
            body_font = ImageFont.truetype("arial.ttf", 28)
            stat_font = ImageFont.truetype("arial.ttf", 72)
        except Exception:
            title_font = body_font = stat_font = ImageFont.load_default()

        # Extract statistics and numbers
        stats = re.findall(r'(\d+(?:\.\d+)?)\s*(?:%|percent|patients?|participants?|weeks?|months?|years?)', content)
        
        if stats:
            # Draw large statistics on right side
            stat_x = w * 0.6
            for i, stat in enumerate(stats[:3]):  # Show up to 3 stats
                y_pos = h * (0.25 + i * 0.25)
                draw.text((stat_x, y_pos), stat, font=stat_font, fill=(20, 80, 120), anchor="mm")
            
            # Draw text on left side only
            text_width = w * 0.5 - 40
        else:
            # If no stats, use full width for text
            text_width = w - 80

        # Wrap and draw main content
        wrapped = textwrap.fill(content, width=int(text_width/10))
        draw.multiline_text(
            (40, h//2), 
            wrapped,
            font=body_font,
            fill=(40, 40, 60),
            anchor="lm"
        )
        
        img.save(path)
        return path

    def generate_audio(self, text, out_path=None):
        """Generate TTS audio for text content."""
        if out_path is None:
            out_path = os.path.join(output_dir, "voice.mp3")
            
        if self.fish_key:
            url = "https://api.fish.audio/v1/audio/generation"
            payload = {"model": "tts-1", "text": text, "voice": "alloy"}
            headers = {"Authorization": f"Bearer {self.fish_key}", "Content-Type": "application/json"}
            
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=60)
                print("Fish status:", r.status_code)
                if r.status_code == 200:
                    with open(out_path, "wb") as f:
                        f.write(r.content)
                    return out_path
            except Exception as e:
                print("Fish TTS failed:", e)

        if pyttsx3 is not None and USE_LOCAL_TTS:
            return self._local_tts(text, out_path)
        
        return self._silent_wav()

    def _local_tts(self, text, out_path):
        """Generate audio using local pyttsx3."""
        if pyttsx3 is None:
            raise RuntimeError("pyttsx3 not available")
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        return out_path

    def _silent_wav(self):
        """Generate silent audio as last resort."""
        import wave, struct
        wav_path = os.path.join(output_dir, "silent.wav")
        framerate = 22050
        nframes = framerate * 2
        with wave.open(wav_path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(framerate)
            silence = struct.pack("h", 0)
            wf.writeframes(silence * nframes)
        return wav_path

    def _create_fallback_slide(self, text, path):
        """Create simple text slide as fallback."""
        w, h = 1280, 720
        img = Image.new("RGB", (w, h), (245, 245, 250))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except Exception:
            font = ImageFont.load_default()
        wrapped = textwrap.fill(text, width=60)
        draw.multiline_text((w//2, h//2), wrapped, font=font, fill=(40, 40, 60),
                           anchor="mm", align="center")
        img.save(path)
        return path

def parse_paper_file(path):
    """Parse and clean paper content."""
    def clean_text(s):
        if not s:
            return ""
        s = s.replace('\\n', ' ').replace('\n', ' ').replace('\r', ' ')
        s = re.sub(r'-{2,}', ' ', s)
        s = ''.join(ch for ch in s if ch.isprintable())
        return re.sub(r'\s+', ' ', s).strip()

    text = open(path, "r", encoding="utf-8").read()
    parts = re.split(r"-{5,}", text)
    sections = []

    for part in parts:
        if not part.strip():
            continue
        
        m_cat = re.search(r"Category:\s*(.+)", part)
        title = clean_text(m_cat.group(1)) if m_cat else "Section"
        
        m_cont = re.search(r"Content:\s*(.+?)(?:Duration|Agent Functions:|\Z)", part, flags=re.S)
        content = clean_text(m_cont.group(1)) if m_cont else ""
        
        if not content:
            continue

        sections.append({
            "title": title,
            "content": content
        })

    return sections

if __name__ == "__main__":
    sample_path = os.path.join(os.path.dirname(__file__), "paper_1_sample.txt")
    if not os.path.exists(sample_path):
        raise SystemExit(f"sample text not found: {sample_path}")

    sections = parse_paper_file(sample_path)
    agent = AIVideoAgent(FISH_API_KEY)

    # Generate slides based on content type
    slide_paths = []
    audio_paths = []
    
    for i, section in enumerate(sections, start=1):
        print(f"\nProcessing section {i}: {section['title']}")
        
        # Generate appropriate slide type
        if agent.is_mechanism_section(section["content"], section["title"]):
            print("→ Generating mechanism visualization")
            img_path = agent.generate_mechanism_image(section["content"], i)
        else:
            print("→ Generating trial info slide")
            img_path = agent.generate_trial_slide(section["content"], i)
            
        slide_paths.append(img_path)
        
        # Generate audio for all sections
        audio_out = os.path.join(output_dir, f"audio_{i}.wav")
        print(f"→ Generating audio")
        aud_path = agent.generate_audio(section["content"], audio_out)
        audio_paths.append(aud_path)

    # Save manifest
    manifest = {
        "slides": [
            {
                "index": i,
                "title": section["title"],
                "type": "mechanism" if agent.is_mechanism_section(section["content"], section["title"]) else "trial",
                "image": slide_paths[i-1],
                "audio": audio_paths[i-1]
            }
            for i, section in enumerate(sections, start=1)
        ]
    }

    manifest_path = os.path.join(output_dir, "slides_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Generated {len(manifest['slides'])} slides + audio files")
    print(f"✅ Manifest: {manifest_path}")
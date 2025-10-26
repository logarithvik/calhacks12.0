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

# compute output dir locally
output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True)

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

    def generate_images(self, prompts):
        """Generate one PNG per prompt, return list of paths."""
        paths = []
        os.makedirs(output_dir, exist_ok=True)
        for i, prompt in enumerate(prompts, start=1):
            amoeba_style = (
                "A colorful, cartoon-style educational illustration in the style of the Amoeba Sisters YouTube videos. "
                "Use friendly rounded shapes, bright pastel colors, thick outlines, and simple cell-like characters with expressive faces. "
                "The scene should explain a biological mechanism clearly using labeled arrows, minimal text, and a cheerful science-classroom tone. "
                "Simple, uncluttered background focusing on clarity and visual humor."
            )
            full_prompt = f"{prompt}. {amoeba_style}"
            path = os.path.join(output_dir, f"slide_{i}.png")
            print(f"[Image] {i}/{len(prompts)}: {full_prompt[:200]}...")
            try:
                if self.image_model:
                    try:
                        self.image_model(full_prompt, save=True, file=path)
                    except Exception:
                        self.image_model(prompt=full_prompt, save=True, file=path)
                    paths.append(path)
                    continue
                else:
                    url = f"https://pollinations.ai/p/{requests.utils.quote(full_prompt)}?width=1280&height=720&nologo=true"
                    r = requests.get(url, timeout=30)
                    if r.status_code == 200:
                        img = Image.open(BytesIO(r.content)).convert("RGB")
                        img.save(path)
                        paths.append(path)
                        continue
                    else:
                        raise Exception(f"Pollinations API error {r.status_code}")
            except Exception as e:
                print("Pollinations generation failed:", e)
                try:
                    self._create_slide_image(prompt, path)
                except Exception as ee:
                    print("Fallback slide render failed:", ee)
                paths.append(path)
        return paths

    def generate_audio(self, text, out_path=None):
        """Generate TTS for `text`. Returns path to audio file (mp3 or wav)."""
        if out_path is None:
            out_path = os.path.join(output_dir, "voice.mp3")
        # Try Fish TTS
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
                else:
                    try:
                        j = r.json()
                        audio_url = j.get("url") or j.get("audio_url")
                        if audio_url:
                            rr = requests.get(audio_url, timeout=60)
                            if rr.status_code == 200:
                                with open(out_path, "wb") as f:
                                    f.write(rr.content)
                                return out_path
                    except Exception:
                        pass
                    print(f"Fish TTS returned {r.status_code}; falling back")
            except Exception as e:
                print("Fish TTS failed:", e)

        # Fallback to local TTS if available
        if pyttsx3 is not None and USE_LOCAL_TTS:
            try:
                wav_path = out_path if out_path.lower().endswith(".wav") else out_path.rsplit(".", 1)[0] + ".wav"
                return self._local_tts(text, out_path=wav_path)
            except Exception as e:
                print("local pyttsx3 failed:", e)

        # Last resort: silent WAV
        return self._silent_wav()

    def _local_tts(self, text, out_path):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        if pyttsx3 is None:
            raise RuntimeError("pyttsx3 not available")
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        return out_path

    def _silent_wav(self):
        import wave, struct
        wav_path = os.path.join(output_dir, "voice_silence.wav")
        framerate = 22050
        nframes = framerate * 2
        with wave.open(wav_path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(framerate)
            silence = struct.pack("h", 0)
            wf.writeframes(silence * nframes)
        return wav_path

    def _create_slide_image(self, text, path, title=None):
        """Simple PIL-based slide renderer fallback."""
        w, h = 1280, 720
        bg = (255, 255, 255)
        img = Image.new("RGB", (w, h), bg)
        draw = ImageDraw.Draw(img)
        try:
            font_title = ImageFont.truetype("arial.ttf", 28)
            font_body = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
        if title:
            draw.text((40, 20), title, fill=(20, 20, 60), font=font_title)
        wrapped = textwrap.fill((text or "").replace("\n", " "), width=70)
        draw.multiline_text((40, 80), wrapped, fill=(40, 40, 60), font=font_body)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path)
        return path


def parse_paper_file(path):
    """Return list of sections: [{'title': str, 'content': str, 'agent_functions': str}, ...]"""
    text = open(path, "r", encoding="utf-8").read()
    parts = re.split(r"-{5,}", text)
    sections = []
    for part in parts:
        if not part.strip():
            continue
        m_cat = re.search(r"Category:\s*(.+)", part)
        title = m_cat.group(1).strip() if m_cat else "Section"
        m_cont = re.search(r"Content:\s*(.+?)(?:Duration|Agent Functions:|\Z)", part, flags=re.S)
        content = m_cont.group(1).strip() if m_cont else ""
        m_af = re.search(r"Agent Functions:\s*(.+)", part, flags=re.S)
        agent_functions = ""
        if m_af:
            agent_functions = m_af.group(1).strip()
            agent_functions = re.sub(r"^\s*-\s*", "", agent_functions, flags=re.M)
            agent_functions = re.sub(r"\s+", " ", agent_functions).strip()
        content = re.sub(r"\s+", " ", content).strip()
        if content:
            sections.append({"title": title, "content": content, "agent_functions": agent_functions})
    return sections


if __name__ == "__main__":
    # Main: parse file, generate images + audio, write manifest for external stitching
    sample_path = os.path.join(os.path.dirname(__file__), "paper_2_sample.txt")
    if not os.path.exists(sample_path):
        raise SystemExit(f"sample text not found: {sample_path}")

    sections = parse_paper_file(sample_path)
    if not sections:
        raise SystemExit("No sections parsed from sample file.")

    agent = AIVideoAgent(FISH_API_KEY)

    slide_prompts = []
    for s in sections:
        prompt = s["content"]
        if s["agent_functions"]:
            prompt += " Visual instructions: " + s["agent_functions"]
        slide_prompts.append(prompt)

    # 1) generate images
    image_paths = agent.generate_images(slide_prompts)

    # 2) generate per-slide audio files
    manifest = []
    for i, s in enumerate(sections, start=1):
        img_path = image_paths[i - 1] if i - 1 < len(image_paths) else None
        audio_out = os.path.join(output_dir, f"slide_{i}.wav")
        print(f"[Audio] slide {i}: generating voice for '{s['title'][:40]}'")
        # prefer local TTS for per-slide narration if available
        if pyttsx3 is not None and USE_LOCAL_TTS:
            aud_path = agent._local_tts(s["content"], out_path=audio_out)
        else:
            aud_path = agent.generate_audio(s["content"], out_path=audio_out.replace(".wav", ".mp3"))
        manifest.append({
            "index": i,
            "title": s["title"],
            "content": s["content"],
            "image": img_path,
            "audio": aud_path
        })

    # 3) save manifest JSON for external stitching
    manifest_path = os.path.join(output_dir, "slides_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"✅ Generated {len(manifest)} slides + audio files in {output_dir}")
    print(f"✅ Manifest: {manifest_path}")
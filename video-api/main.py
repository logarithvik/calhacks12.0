import os
import requests
import time
import nltk
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap

# Optional local TTS and diagram libs
try:
    import pyttsx3
except Exception:
    pyttsx3 = None
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import networkx as nx
except Exception:
    plt = None
    nx = None

# Load .env variables
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
FISH_API_KEY = os.getenv("FISH_API_KEY")

# Ensure punkt is available for sentence tokenization. If not, download it.
nltk.download("punkt", quiet=True)

# Use local TTS fallback if FISH fails or USE_LOCAL_TTS env is set to '1'
USE_LOCAL_TTS = os.getenv("USE_LOCAL_TTS", "1") in ("1", "true", "True")


class AIVideoAgent:
    def __init__(self, hf_token, fish_key):
        self.hf_token = hf_token
        self.fish_key = fish_key

    def generate_images(self, sentences):
        paths = []
        for i, text in enumerate(sentences):
            prompt = f"{text}, cinematic digital art, soft lighting"
            print(f"[Image] {i+1}/{len(sentences)}: {prompt}")
            used_hf = False
            try:
                r = requests.post(
                    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
                    headers={"Authorization": f"Bearer {self.hf_token}"},
                    json={"inputs": prompt},
                    timeout=30,
                )
                print("HF status:", r.status_code)
                print("HF response:", r.text[:300])

                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content))
                    os.makedirs("output", exist_ok=True)
                    path = f"output/frame_{i+1}.png"
                    img.save(path)
                    paths.append(path)
                    used_hf = True
            except Exception as e:
                print("HF request failed:", e)

            if not used_hf:
                # Create a richer slide-style image with text + simple diagram
                os.makedirs("output", exist_ok=True)
                path = f"output/frame_{i+1}.png"
                self._create_slide_image(text, path, index=i + 1)
                paths.append(path)

        return paths

    def generate_audio(self, text):
        url = "https://api.fish.audio/v1/audio/generation"
        payload = {"model": "tts-1", "text": text, "voice": "alloy"}
        headers = {"Authorization": f"Bearer {self.fish_key}", "Content-Type": "application/json"}
        # Try remote Fish TTS first
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            print("Fish status:", r.status_code)
            print("Fish response:", r.text[:300])

            if r.status_code == 200:
                os.makedirs("output", exist_ok=True)
                path = "output/voice.mp3"
                with open(path, "wb") as f:
                    f.write(r.content)
                return path
            else:
                raise Exception(f"TTS error: {r.text}")
        except Exception as e:
            print("TTS remote failed:", e)
            if USE_LOCAL_TTS and pyttsx3 is not None:
                try:
                    print("Using local pyttsx3 TTS fallback")
                    return self._local_tts(text)
                except Exception as e2:
                    print("Local TTS failed:", e2)

            # Final fallback: 2 seconds silence WAV
            os.makedirs("output", exist_ok=True)
            wav_path = "output/voice_silence.wav"
            try:
                import wave, struct

                framerate = 22050
                nframes = framerate * 2  # 2 seconds of silence
                with wave.open(wav_path, "w") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(framerate)
                    silence = struct.pack("h", 0)
                    wf.writeframes(silence * nframes)
                return wav_path
            except Exception as e2:
                raise Exception(f"TTS fallback failed: {e2}")

    def compose_video(self, image_paths, audio_path, total_duration=60):
        if not image_paths:
            raise ValueError("No image paths provided to compose_video")
        each = total_duration / len(image_paths)
        clips = [ImageClip(p, duration=each) for p in image_paths]
        video = concatenate_videoclips(clips, method="compose")
        audio = AudioFileClip(audio_path)
        # moviepy API may provide with_audio instead of set_audio depending on version
        if hasattr(video, "with_audio"):
            final = video.with_audio(audio)
        else:
            final = video.set_audio(audio)
        os.makedirs("output", exist_ok=True)
        output_path = "output/final_video.mp4"
        final.write_videofile(output_path, fps=24)
        return output_path

    def create_video(self, text):
        sentences = sent_tokenize(text)
        sentences = sentences[:10]
        imgs = self.generate_images(sentences)
        audio = self.generate_audio(text)
        video_path = self.compose_video(imgs, audio)
        print(f"✅ Video ready: {video_path}")

    # ------------------ helpers for local fallbacks ------------------
    def _local_tts(self, text, out_path="output/voice_local.wav"):
        """Create local TTS using pyttsx3 (Windows SAPI) and return path."""
        if pyttsx3 is None:
            raise RuntimeError("pyttsx3 not installed")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        engine = pyttsx3.init()
        # Optional: adjust voice properties
        engine.setProperty('rate', 150)
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        return out_path

    def _create_slide_image(self, text, out_path, index=1):
        """Create a slide-like image (text + simple diagram) with PIL and matplotlib/networkx if available."""
        W, H = 1280, 720
        bg = (245, 245, 250)
        img = Image.new("RGB", (W, H), color=bg)
        draw = ImageDraw.Draw(img)
        try:
            font_title = ImageFont.truetype("arial.ttf", 42)
        except Exception:
            font_title = ImageFont.load_default()
        try:
            font_body = ImageFont.truetype("arial.ttf", 22)
        except Exception:
            font_body = ImageFont.load_default()

        # Title: first short chunk
        title = (text or "Slide")[:60]
        draw.text((40, 30), title, font=font_title, fill=(20, 20, 40))

        # Body: wrap remaining text
        body = text.replace('\n', ' ')
        wrapped = textwrap.fill(body, width=60)
        draw.text((40, 100), wrapped, font=font_body, fill=(40, 40, 60))

        # Add a simple diagram on the right if networkx/matplotlib available
        if plt is not None and nx is not None:
            try:
                fig = plt.figure(figsize=(4, 3), dpi=100)
                G = nx.DiGraph()
                # Create a small illustrative graph based on words
                words = [w.strip('.,') for w in title.split()[:6]]
                if not words:
                    words = ["A","B","C"]
                for i, w in enumerate(words):
                    G.add_node(i, label=w)
                for i in range(len(words)-1):
                    G.add_edge(i, i+1)
                pos = nx.spring_layout(G)
                nx.draw(G, pos, with_labels=True, labels={i: d['label'] for i,d in G.nodes(data=True)}, node_color='#66c2a5')
                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png', bbox_inches='tight')
                plt.close(fig)
                buf.seek(0)
                diag = Image.open(buf).convert('RGB')
                diag = diag.resize((420, 300))
                img.paste(diag, (820, 80))
            except Exception as e:
                print("diagram render failed:", e)

        img.save(out_path)


if __name__ == "__main__":
    text = """Clinical trials help scientists test new drugs safely.
    Participants receive close medical care and help advance medicine.
    Each phase builds on the previous to measure safety, dosage, and effectiveness."""

    agent = AIVideoAgent(HF_TOKEN, FISH_API_KEY)
    agent.create_video(text)


if __name__ == "__main__":
    text = """Clinical trials help scientists test new drugs safely.
    Participants receive close medical care and help advance medicine.
    Each phase builds on the previous to measure safety, dosage, and effectiveness."""

    agent = AIVideoAgent(HF_TOKEN, FISH_API_KEY)
    agent.create_video(text)
import os
import requests
import time
import nltk
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap

# Optional local TTS and diagram libs
try:
    import pyttsx3
except Exception:
    pyttsx3 = None
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import networkx as nx
except Exception:
    plt = None
    nx = None

# Load .env variables
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
FISH_API_KEY = os.getenv("FISH_API_KEY")

# Ensure punkt is available for sentence tokenization. If not, download it.
nltk.download("punkt", quiet=True)

# Use local TTS fallback if FISH fails or USE_LOCAL_TTS env is set to '1'
USE_LOCAL_TTS = os.getenv("USE_LOCAL_TTS", "1") in ("1", "true", "True")



class AIVideoAgent:
    def __init__(self, hf_token, fish_key):
        self.hf_token = hf_token
        self.fish_key = fish_key

    def generate_images(self, sentences):
        paths = []
        for i, text in enumerate(sentences):
            prompt = f"{text}, cinematic digital art, soft lighting"
            print(f"[Image] {i+1}/{len(sentences)}: {prompt}")
            used_hf = False
            try:
                r = requests.post(
                    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
                    headers={"Authorization": f"Bearer {self.hf_token}"},
                    json={"inputs": prompt},
                    timeout=30,
                )
                print("HF status:", r.status_code)
                print("HF response:", r.text[:300])

                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content))
                    os.makedirs("output", exist_ok=True)
                    path = f"output/frame_{i+1}.png"
                    img.save(path)
                    paths.append(path)
                    used_hf = True
            except Exception as e:
                print("HF request failed:", e)

            if not used_hf:
                # Create a richer slide-style image with text + simple diagram
                os.makedirs("output", exist_ok=True)
                path = f"output/frame_{i+1}.png"
                self._create_slide_image(text, path, index=i + 1)
                paths.append(path)

        return paths

    def generate_audio(self, text):
        url = "https://api.fish.audio/v1/audio/generation"
        payload = {"model": "tts-1", "text": text, "voice": "alloy"}
        headers = {"Authorization": f"Bearer {self.fish_key}", "Content-Type": "application/json"}
        # Try remote Fish TTS first
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            print("Fish status:", r.status_code)
            print("Fish response:", r.text[:300])

            if r.status_code == 200:
                os.makedirs("output", exist_ok=True)
                path = "output/voice.mp3"
                with open(path, "wb") as f:
                    f.write(r.content)
                return path
            else:
                raise Exception(f"TTS error: {r.text}")
        except Exception as e:
            print("TTS remote failed:", e)
            if USE_LOCAL_TTS and pyttsx3 is not None:
                try:
                    print("Using local pyttsx3 TTS fallback")
                    return self._local_tts(text)
                except Exception as e2:
                    print("Local TTS failed:", e2)

            # Final fallback: 2 seconds silence WAV
            os.makedirs("output", exist_ok=True)
            wav_path = "output/voice_silence.wav"
            try:
                import wave, struct

                framerate = 22050
                nframes = framerate * 2  # 2 seconds of silence
                with wave.open(wav_path, "w") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(framerate)
                    silence = struct.pack("h", 0)
                    wf.writeframes(silence * nframes)
                return wav_path
            except Exception as e2:
                raise Exception(f"TTS fallback failed: {e2}")

    def compose_video(self, image_paths, audio_path, total_duration=60):
        if not image_paths:
            raise ValueError("No image paths provided to compose_video")
        each = total_duration / len(image_paths)
        clips = [ImageClip(p, duration=each) for p in image_paths]
        video = concatenate_videoclips(clips, method="compose")
        audio = AudioFileClip(audio_path)
        # moviepy API may provide with_audio instead of set_audio depending on version
        if hasattr(video, "with_audio"):
            final = video.with_audio(audio)
        else:
            final = video.set_audio(audio)
        os.makedirs("output", exist_ok=True)
        output_path = "output/final_video.mp4"
        final.write_videofile(output_path, fps=24)
        return output_path

    def create_video(self, text):
        sentences = sent_tokenize(text)
        sentences = sentences[:10]
        imgs = self.generate_images(sentences)
        audio = self.generate_audio(text)
        video_path = self.compose_video(imgs, audio)
        print(f"✅ Video ready: {video_path}")

    # ------------------ helpers for local fallbacks ------------------
    def _local_tts(self, text, out_path="output/voice_local.wav"):
        """Create local TTS using pyttsx3 (Windows SAPI) and return path."""
        if pyttsx3 is None:
            raise RuntimeError("pyttsx3 not installed")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        engine = pyttsx3.init()
        # Optional: adjust voice properties
        engine.setProperty('rate', 150)
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        return out_path

    def _create_slide_image(self, text, out_path, index=1):
        """Create a slide-like image (text + simple diagram) with PIL and matplotlib/networkx if available."""
        W, H = 1280, 720
        bg = (245, 245, 250)
        img = Image.new("RGB", (W, H), color=bg)
        draw = ImageDraw.Draw(img)
        try:
            font_title = ImageFont.truetype("arial.ttf", 42)
        except Exception:
            font_title = ImageFont.load_default()
        try:
            font_body = ImageFont.truetype("arial.ttf", 22)
        except Exception:
            font_body = ImageFont.load_default()

        # Title: first short chunk
        title = (text or "Slide")[:60]
        draw.text((40, 30), title, font=font_title, fill=(20, 20, 40))

        # Body: wrap remaining text
        body = text.replace('\n', ' ')
        wrapped = textwrap.fill(body, width=60)
        draw.text((40, 100), wrapped, font=font_body, fill=(40, 40, 60))

        # Add a simple diagram on the right if networkx/matplotlib available
        if plt is not None and nx is not None:
            try:
                fig = plt.figure(figsize=(4, 3), dpi=100)
                G = nx.DiGraph()
                # Create a small illustrative graph based on words
                words = [w.strip('.,') for w in title.split()[:6]]
                if not words:
                    words = ["A","B","C"]
                for i, w in enumerate(words):
                    G.add_node(i, label=w)
                for i in range(len(words)-1):
                    G.add_edge(i, i+1)
                pos = nx.spring_layout(G)
                nx.draw(G, pos, with_labels=True, labels={i: d['label'] for i,d in G.nodes(data=True)}, node_color='#66c2a5')
                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png', bbox_inches='tight')
                plt.close(fig)
                buf.seek(0)
                diag = Image.open(buf).convert('RGB')
                diag = diag.resize((420, 300))
                img.paste(diag, (820, 80))
            except Exception as e:
                print("diagram render failed:", e)

        img.save(out_path)


if __name__ == "__main__":
    text = """Clinical trials help scientists test new drugs safely.
    Participants receive close medical care and help advance medicine.
    Each phase builds on the previous to measure safety, dosage, and effectiveness."""

    agent = AIVideoAgent(HF_TOKEN, FISH_API_KEY)
    agent.create_video(text)
import os
import requests
import time
import nltk
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image
from io import BytesIO

# Load .env variables
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
FISH_API_KEY = os.getenv("FISH_API_KEY")

# Ensure punkt is available for sentence tokenization. If not, download it.
nltk.download("punkt", quiet=True)


class AIVideoAgent:
    def __init__(self, hf_token, fish_key):
        self.hf_token = hf_token
        self.fish_key = fish_key

    def generate_images(self, sentences):
        paths = []
        for i, text in enumerate(sentences):
            prompt = f"{text}, cinematic digital art, soft lighting"
            print(f"[Image] {i+1}/{len(sentences)}: {prompt}")
            try:
                r = requests.post(
                    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
                    headers={"Authorization": f"Bearer {self.hf_token}"},
                    json={"inputs": prompt},
                    timeout=30,
                )
                print("HF status:", r.status_code)
                print("HF response:", r.text[:300])

                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content))
                    os.makedirs("output", exist_ok=True)
                    path = f"output/frame_{i+1}.png"
                    img.save(path)
                    paths.append(path)
                    continue
                else:
                    print("Image error:", r.text)
            except Exception as e:
                print("HF request failed:", e)

            # Fallback: create a simple placeholder image when HF fails or credentials missing
            os.makedirs("output", exist_ok=True)
            path = f"output/frame_{i+1}.png"
            try:
                from PIL import ImageDraw, ImageFont

                img = Image.new("RGB", (1280, 720), color=(30, 30, 30))
                draw = ImageDraw.Draw(img)
                font = ImageFont.load_default()
                msg = (text or "Placeholder")[:200]
                draw.text((50, 50), msg, font=font, fill=(220, 220, 220))
                img.save(path)
            except Exception:
                Image.new("RGB", (1280, 720), color=(30, 30, 30)).save(path)
            paths.append(path)

        return paths

    def generate_audio(self, text):
        url = "https://api.fish.audio/v1/audio/generation"
        payload = {"model": "tts-1", "text": text, "voice": "alloy"}
        headers = {"Authorization": f"Bearer {self.fish_key}", "Content-Type": "application/json"}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            print("Fish status:", r.status_code)
            print("Fish response:", r.text[:300])

            if r.status_code == 200:
                os.makedirs("output", exist_ok=True)
                path = "output/voice.mp3"
                with open(path, "wb") as f:
                    f.write(r.content)
                return path
            else:
                raise Exception(f"TTS error: {r.text}")
        except Exception as e:
            # Fallback: create a short silent WAV so composition can continue locally
            print("TTS fallback due to error:", e)
            os.makedirs("output", exist_ok=True)
            wav_path = "output/voice_silence.wav"
            try:
                import wave, struct

                framerate = 22050
                nframes = framerate * 2  # 2 seconds of silence
                with wave.open(wav_path, "w") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(framerate)
                    silence = struct.pack("h", 0)
                    wf.writeframes(silence * nframes)
                return wav_path
            except Exception as e2:
                raise Exception(f"TTS fallback failed: {e2}")

    def compose_video(self, image_paths, audio_path, total_duration=60):
        if not image_paths:
            raise ValueError("No image paths provided to compose_video")
        each = total_duration / len(image_paths)
        clips = [ImageClip(p, duration=each) for p in image_paths]
        video = concatenate_videoclips(clips, method="compose")
        audio = AudioFileClip(audio_path)
        # moviepy API may provide with_audio instead of set_audio depending on version
        if hasattr(video, "with_audio"):
            final = video.with_audio(audio)
        else:
            final = video.set_audio(audio)
        os.makedirs("output", exist_ok=True)
        output_path = "output/final_video.mp4"
        final.write_videofile(output_path, fps=24)
        return output_path

    def create_video(self, text):
        sentences = sent_tokenize(text)
        sentences = sentences[:10]
        imgs = self.generate_images(sentences)
        audio = self.generate_audio(text)
        video_path = self.compose_video(imgs, audio)
        print(f"✅ Video ready: {video_path}")


if __name__ == "__main__":
    text = """Clinical trials help scientists test new drugs safely.
    Participants receive close medical care and help advance medicine.
    Each phase builds on the previous to measure safety, dosage, and effectiveness."""

    agent = AIVideoAgent(HF_TOKEN, FISH_API_KEY)
    agent.create_video(text)
    agent = AIVideoAgent(HF_TOKEN, FISH_API_KEY)
    agent.create_video(text)

import os
import requests
import nltk
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
from generate_outline_video import create_slide_image, local_tts
# compute output dir locally to avoid importing side-effect constants
output_dir = os.path.join(os.path.dirname(__file__), 'output')
from multiprocessing import freeze_support  # prevents infinite loop during video creation

# Optional local TTS
try:
    import pyttsx3
except Exception:
    pyttsx3 = None

# Pollinations SDK (pip install pollinations)
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

    # ---------- IMAGE GENERATION (Pollinations) ----------
    def generate_images(self, sentences):
        paths = []
        os.makedirs("output", exist_ok=True)

        for i, text in enumerate(sentences):
            prompt = f"{text}, cinematic digital art, soft lighting"
            path = f"output/frame_{i+1}.png"
            print(f"[Image] {i+1}/{len(sentences)}: {prompt}")

            try:
                if self.image_model:
                    self.image_model(prompt, save=True, file=path)
                    paths.append(path)
                    continue
                else:
                    # direct endpoint fallback
                    url = f"https://pollinations.ai/p/{requests.utils.quote(prompt)}?width=1280&height=720&nologo=true"
                    r = requests.get(url, timeout=30)
                    if r.status_code == 200:
                        img = Image.open(BytesIO(r.content))
                        img.save(path)
                        paths.append(path)
                        continue
                    else:
                        raise Exception(f"Pollinations API error {r.status_code}")
            except Exception as e:
                print("Pollinations generation failed:", e)
                self._create_slide_image(text, path)
                paths.append(path)
        return paths

    # ---------- AUDIO GENERATION (Fish Audio) ----------
    def generate_audio(self, text):
        url = "https://api.fish.audio/v1/audio/generation"
        payload = {"model": "tts-1", "text": text, "voice": "alloy"}
        headers = {"Authorization": f"Bearer {self.fish_key}", "Content-Type": "application/json"}

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            print("Fish status:", r.status_code)
            print("Fish response:", r.text[:200])
            if r.status_code == 200:
                path = "output/voice.mp3"
                with open(path, "wb") as f:
                    f.write(r.content)
                return path
            else:
                raise Exception(f"TTS error {r.text}")
        except Exception as e:
            print("Fish TTS failed:", e)
            if USE_LOCAL_TTS and pyttsx3:
                return self._local_tts(text)
            else:
                return self._silent_wav()

    # ---------- VIDEO COMPOSITION ----------
    def compose_video(self, image_paths, audio_path):
        if not image_paths:
            raise ValueError("No images to compose video")

        audio = AudioFileClip(audio_path)
        each = audio.duration / len(image_paths)
        print(f"Composing video: {len(image_paths)} slides, {each:.2f}s each")

        clips = [
            ImageClip(p)
            .resize(width=1280)
            .set_duration(each)
            .fadein(0.7)
            .fadeout(0.7)
            for p in image_paths
        ]
        video = concatenate_videoclips(clips, method="compose", padding=-0.5)
        final = video.set_audio(audio)
        output_path = "output/final_video.mp4"
        final.write_videofile(output_path, fps=24)
        return output_path

    # ---------- MAIN PIPELINE ----------
    def create_video(self, text):
        # Default behavior: try to use Pollinations image generation first,
        # then fall back to outline-style slides if unavailable.
        sentences = sent_tokenize(text)
        os.makedirs(output_dir, exist_ok=True)

        # Try Pollinations-based image generation for the sentences
        try:
            poll_imgs = self.generate_images(sentences)
            if poll_imgs and len(poll_imgs) == len(sentences):
                print("Using Pollinations images for slides")
                # generate per-slide local TTS and assemble
                clips = []
                for i, img_p in enumerate(poll_imgs, start=1):
                    aud_p = os.path.join(output_dir, f"slide_{i}.wav")
                    try:
                        local_tts(sentences[i - 1], aud_p)
                        audio_clip = AudioFileClip(aud_p)
                        clip = ImageClip(img_p)
                        if hasattr(clip, 'set_duration'):
                            clip = clip.set_duration(audio_clip.duration)
                        elif hasattr(clip, 'with_duration'):
                            clip = clip.with_duration(audio_clip.duration)
                        else:
                            raise RuntimeError('No duration setter available on ImageClip')

                        if hasattr(clip, 'set_audio'):
                            clip = clip.set_audio(audio_clip)
                        elif hasattr(clip, 'with_audio'):
                            clip = clip.with_audio(audio_clip)
                        else:
                            print('Warning: could not attach audio to clip')

                        clips.append(clip)
                    except Exception as e:
                        print("Pollinations-path: error building clip:", e)

                if clips:
                    final = concatenate_videoclips(clips, method="compose")
                    out = os.path.join(output_dir, "final_video.mp4")
                    final.write_videofile(out, fps=24)
                    print(f"✅ Video ready: {out}")
                    return out
                else:
                    print("Pollinations images generated but no clips could be assembled; falling back")
        except Exception as e:
            print("Pollinations generation path failed:", e)

        # Fall back: create simple slides + per-slide local TTS (existing behavior)
        image_paths = []
        audio_paths = []
        for i, s in enumerate(sentences, start=1):
            img_path = os.path.join(output_dir, f"slide_{i}.png")
            audio_path = os.path.join(output_dir, f"slide_{i}.wav")
            print(f"[Slide] {i}/{len(sentences)}")
            try:
                create_slide_image(s, img_path, title=None)
            except Exception as e:
                print("create_slide_image failed, falling back:", e)
                self._create_slide_image(s, img_path)

            try:
                local_tts(s, audio_path)
            except Exception as e:
                print("local_tts failed, falling back to Fish or silence:", e)
                audio_paths = []
                break

            image_paths.append(img_path)
            audio_paths.append(audio_path)

        if audio_paths and len(audio_paths) == len(image_paths):
            clips = []
            for img_p, aud_p in zip(image_paths, audio_paths):
                try:
                    audio_clip = AudioFileClip(aud_p)
                    clip = ImageClip(img_p)
                    if hasattr(clip, 'set_duration'):
                        clip = clip.set_duration(audio_clip.duration)
                    elif hasattr(clip, 'with_duration'):
                        clip = clip.with_duration(audio_clip.duration)
                    else:
                        raise RuntimeError('No duration setter available on ImageClip')

                    if hasattr(clip, 'set_audio'):
                        clip = clip.set_audio(audio_clip)
                    elif hasattr(clip, 'with_audio'):
                        clip = clip.with_audio(audio_clip)
                    else:
                        print('Warning: could not attach audio to clip')

                    clips.append(clip)
                except Exception as e:
                    print("Error attaching audio to clip:", e)

            if not clips:
                raise RuntimeError("No clips were assembled")

            final = concatenate_videoclips(clips, method="compose")
            out = os.path.join(output_dir, "final_video.mp4")
            final.write_videofile(out, fps=24)
            print(f"✅ Video ready: {out}")
            return out

        # Last-resort: generate images via Pollinations for a smaller set and a single Fish audio track
        sentences = sentences[:10]
        imgs = self.generate_images(sentences)
        audio = self.generate_audio(text)
        video_path = self.compose_video(imgs, audio)
        print(f"✅ Video ready: {video_path}")

    # ---------- FALLBACK HELPERS ----------
    def _create_slide_image(self, text, path):
        img = Image.new("RGB", (1280, 720), color=(245, 245, 250))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 26)
        except Exception:
            font = ImageFont.load_default()
        wrapped = textwrap.fill(text, width=70)
        draw.text((40, 100), wrapped, font=font, fill=(40, 40, 60))
        img.save(path)

    def _local_tts(self, text, out_path="output/voice_local.wav"):
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        return out_path

    def _silent_wav(self):
        import wave, struct
        wav_path = "output/voice_silence.wav"
        framerate = 22050
        nframes = framerate * 2
        with wave.open(wav_path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(framerate)
            silence = struct.pack("h", 0)
            wf.writeframes(silence * nframes)
        return wav_path


# ---------- MAIN EXECUTION ----------
if __name__ == "__main__":
    freeze_support()  # fixes infinite loop when using MoviePy + multiprocessing

    text = """Clinical trials help scientists test new drugs safely.
    Participants receive close medical care and help advance medicine.
    Each phase builds on the previous to measure safety, dosage, and effectiveness."""

    agent = AIVideoAgent(FISH_API_KEY)
    agent.create_video(text)

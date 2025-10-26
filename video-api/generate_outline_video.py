
import os
import textwrap
from io import BytesIO
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

# Local helper: create a slide image (title + wrapped body + optional simple diagram)
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import networkx as nx
except Exception:
    plt = None
    nx = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None


def create_slide_image(text, out_path, title=None):
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

    title_text = title or (text or "Slide")[:60]
    draw.text((40, 30), title_text, font=font_title, fill=(20, 20, 40))

    body = (text or "").replace('\n', ' ')
    wrapped = textwrap.fill(body, width=60)
    draw.text((40, 100), wrapped, font=font_body, fill=(40, 40, 60))

    # Optional diagram
    if plt is not None and nx is not None:
        try:
            fig = plt.figure(figsize=(4, 3), dpi=100)
            G = nx.path_graph(4)
            nx.draw(G, with_labels=True, node_color='#66c2a5')
            buf = BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            diag = Image.open(buf).convert('RGB')
            diag = diag.resize((420, 300))
            img.paste(diag, (820, 80))
        except Exception as e:
            print('diagram error', e)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)


def local_tts(text, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if pyttsx3 is not None:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        return out_path
    # fallback: silent wav
    import wave, struct
    framerate = 22050
    nframes = framerate * 2
    with wave.open(out_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(struct.pack('h', 0) * nframes)
    return out_path


# Slides (title optional) — derived from user's outline
slides = [
    ("Impact", "Significance: Second most common malignancy in the US. Hundreds of thousands affected. Incidence doubled from 1994 to 2006.", 8),
    ("Purpose", "This study tests cemiplimab, a human monoclonal antibody targeting the PD-1 immune checkpoint. PD-1 acts as a brake on immune cells; blocking it helps the immune system attack cancer. (Analogy: removing a brake so the immune car can move.)", 12),
    ("Who Can Participate", "Adults 18+ with confirmed invasive CSCC. Additional eligibility checks include overall health and tumor characteristics.", 5),
    ("What Participation Involves", "Screening up to 4 weeks (blood tests, imaging, ECG, biopsies). Treatment: IV cemiplimab every 2–4 weeks for 48–108 weeks, possible switch to subcutaneous injections after 27 weeks if stable. Follow-up for 6 months to 1.5 years.", 15),
    ("Flowchart", "Screening → Enrollment → Treatment cycles → Assessment → Follow-up (months).", 15),
    ("Possible Benefits", "Cemiplimab may shrink or control tumors and provides close medical monitoring for participants.", 10),
    ("Possible Side Effects", "Immune-related side effects: fatigue, rash, diarrhea, fever, organ inflammation (liver, lungs, colon, thyroid). Severe events are possible; you may stop treatment at any time.", 15),
    ("Confidentiality & Ethics", "This study follows GCP and the Declaration of Helsinki. Your safety and privacy are priorities. For participant rights visit the provided link.", 10),
    ("Contact", "Conducted by Regeneron Pharmaceuticals, Inc. For questions contact the study team at: [Insert contact details].", 7),
]

output_dir = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(output_dir, exist_ok=True)

clips = []
for i, (title, text, dur) in enumerate(slides, start=1):
    img_path = os.path.join(output_dir, f'slide_{i}.png')
    create_slide_image(text, img_path, title=title)
    audio_path = os.path.join(output_dir, f'slide_{i}.wav')
    local_tts(text, audio_path)

    clip = ImageClip(img_path)
    # moviepy API compatibility: prefer set_duration, fallback to with_duration
    if hasattr(clip, 'set_duration'):
        clip = clip.set_duration(dur)
    elif hasattr(clip, 'with_duration'):
        clip = clip.with_duration(dur)
    else:
        raise RuntimeError('No duration setter available on ImageClip')

    audio = AudioFileClip(audio_path)
    # audio setter compatibility
    if hasattr(clip, 'set_audio'):
        clip = clip.set_audio(audio)
    elif hasattr(clip, 'with_audio'):
        clip = clip.with_audio(audio)
    else:
        print('Warning: could not attach audio to clip')
    clips.append(clip)

final = concatenate_videoclips(clips, method='compose')
final_path = os.path.join(output_dir, 'outline_video.mp4')
final.write_videofile(final_path, fps=24)

print('Generated:', final_path)

import argparse
import sys
from pathlib import Path
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips


def stitch_slides(images_dir: Path, audio_file: Path | None, out_file: Path, width: int = 1280, fps: int = 24):
    # Prefer slide_*.png / slide_*.jpg if present (matches per-slide audio naming)
    slide_pngs = sorted(images_dir.glob("slide_*.png"))
    slide_jpgs = sorted(images_dir.glob("slide_*.jpg"))
    if slide_pngs or slide_jpgs:
        images = slide_pngs + slide_jpgs
    else:
        images = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg"))
    images = [p for p in images if p.is_file()]
    if not images:
        raise SystemExit(f"No images found in {images_dir}")

    # Detect per-slide audio files that match image stems (e.g., slide_1.png -> slide_1.wav)
    per_slide_audio = []
    for img in images:
        found = None
        for ext in ('.wav', '.mp3', '.m4a'):
            cand = images_dir / (img.stem + ext)
            if cand.exists():
                found = cand
                break
        per_slide_audio.append(found)

    use_per_slide = all(a is not None for a in per_slide_audio)

    if use_per_slide:
        print(f"Found per-slide audio for all {len(images)} images; using per-slide durations")
        clips = []
        for img, aud in zip(images, per_slide_audio):
            audio = AudioFileClip(str(aud))
            clip = ImageClip(str(img))
            # resize compatibility
            if hasattr(clip, 'resize'):
                clip = clip.resize(width=width)
            elif hasattr(clip, 'resized'):
                clip = clip.resized(width=width)
            else:
                try:
                    clip = clip.fx('resize', width=width)
                except Exception:
                    pass

            # set duration based on audio length
            if hasattr(clip, 'set_duration'):
                clip = clip.set_duration(audio.duration)
            elif hasattr(clip, 'with_duration'):
                clip = clip.with_duration(audio.duration)

            # attach audio
            if hasattr(clip, 'set_audio'):
                clip = clip.set_audio(audio)
            elif hasattr(clip, 'with_audio'):
                clip = clip.with_audio(audio)
            else:
                print('Warning: could not attach per-slide audio to clip')

            clips.append(clip)

        final = concatenate_videoclips(clips, method="compose")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        print(f"Writing video to {out_file}")
        final.write_videofile(str(out_file), fps=fps)
        return

    # Fallback: require a single audio file and split evenly across slides
    if audio_file is None or not audio_file.exists():
        raise SystemExit("No per-slide audios found and no single audio file provided")

    audio = AudioFileClip(str(audio_file))
    total = audio.duration
    per = total / len(images)
    print(f"Found {len(images)} images, audio duration {total:.2f}s -> {per:.2f}s per slide")

    clips = []
    for img in images:
        clip = ImageClip(str(img))
        # compatibility: different moviepy versions use resize or resized
        if hasattr(clip, 'resize'):
            clip = clip.resize(width=width)
        elif hasattr(clip, 'resized'):
            clip = clip.resized(width=width)
        else:
            try:
                clip = clip.fx('resize', width=width)
            except Exception:
                # fallback: ignore resizing
                pass
        # compatibility: prefer set_duration
        if hasattr(clip, 'set_duration'):
            clip = clip.set_duration(per)
        elif hasattr(clip, 'with_duration'):
            clip = clip.with_duration(per)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    # compatibility: set_audio or with_audio
    if hasattr(video, 'set_audio'):
        video = video.set_audio(audio)
    elif hasattr(video, 'with_audio'):
        video = video.with_audio(audio)
    else:
        print('Warning: could not attach audio to final video (no set_audio/with_audio)')
    out_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing video to {out_file}")
    video.write_videofile(str(out_file), fps=fps)


def main(argv=None):
    p = argparse.ArgumentParser(description="Stitch slide images and a single audio file into a video")
    p.add_argument("--images-dir", type=Path, default=Path("output"), help="Directory containing slide images (*.png/*.jpg)")
    p.add_argument("--audio", type=Path, default=Path("output/voice.mp3"), help="Audio file to attach")
    p.add_argument("--out", type=Path, default=Path("output/stitched_video.mp4"), help="Output video path")
    p.add_argument("--width", type=int, default=1280, help="Video width (px)")
    p.add_argument("--fps", type=int, default=24, help="Output fps")
    args = p.parse_args(argv)

    stitch_slides(args.images_dir, args.audio, args.out, width=args.width, fps=args.fps)


if __name__ == "__main__":
    main()

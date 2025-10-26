# Video Generation Workflow Guide

## Overview

The video generation feature creates patient-friendly educational videos from clinical trial summaries using a sophisticated 7-stage agentic workflow.

## Architecture

### Backend Integration

**Location:** `/backend/app/agents/video_agent/`

The video agent is fully integrated with the main workflow in `video_agent.py`, which orchestrates all stages from `agent.py`:

1. **Stage 1: Script Generation**
   - Uses Gemini AI with `video_transcript_generation_prompt.txt`
   - Creates video script with segments, narration, and timing
   - Output: `step1_script.json`

2. **Stage 2: Visual Asset Extraction**
   - Uses Gemini AI with `video_asset_generation_prompt.txt`
   - Defines visual elements needed for each segment
   - Output: `step2_assets.json`

3. **Stage 3: Image Generation**
   - Uses Pollinations AI to generate images
   - Implements retry logic with prompt simplification
   - Output: PNG images in `images/` directory

4. **Stage 4: Background Removal**
   - Uses rembg library for transparent backgrounds
   - Optional stage (skipped if rembg not available)
   - Output: PNG images in `images/no_bg/` directory

5. **Stage 5: Slide Layout Planning**
   - Uses Gemini AI with `canvaa_prompts.txt`
   - Plans composition, positioning, and timing
   - Output: `step4_slides.json`

6. **Stage 6: Slide Creation**
   - Uses ffmpeg + PIL for professional slides
   - Composites images, text, and styling
   - Output: PNG slides in `slides/` directory

7. **Stage 7: Video Composition**
   - Uses ffmpeg for final video assembly
   - Adds narration with TTS (ElevenLabs or pyttsx3)
   - Optional background music
   - Output: `final_video.mp4`

### Output Structure

All outputs are organized per trial:

```
uploads/video_outputs/trial_{id}/
├── {timestamp}/
│   ├── outputs/
│   │   ├── input_summary.txt
│   │   ├── step1_script.json
│   │   ├── step2_assets.json
│   │   └── step4_slides.json
│   ├── images/
│   │   ├── *.png (original images)
│   │   └── no_bg/
│   │       └── *_nobg.png (transparent backgrounds)
│   ├── slides/
│   │   └── slide_*.png
│   ├── prompts/
│   │   └── *.txt (copies of all prompts used)
│   ├── final_video.mp4
│   └── metadata.json
```

### Frontend Integration

**Location:** `/frontend/src/pages/VideoViewer.jsx`

Features:
- Full video player with custom controls
- Download video functionality
- Display of production metadata (segments, assets, slides)
- Links to download intermediate outputs (script, assets, metadata)
- Responsive design with gradient styling

**Route:** `/trial/:id/video/:contentId`

## API Endpoints

### Generate Video

```http
POST /api/generate/video/{trial_id}
```

**Prerequisites:** Summary must be generated first

**Response:**
```json
{
  "id": 1,
  "trial_id": 1,
  "content_type": "video",
  "file_path": "uploads/video_outputs/trial_1/20231026_123456/final_video.mp4",
  "content_text": "{\"status\": \"success\", \"metadata\": {...}}",
  "version": 1,
  "created_at": "2023-10-26T12:34:56",
  "updated_at": "2023-10-26T12:34:56"
}
```

### View Video Content

```http
GET /api/generate/content/{content_id}/data
```

**Response:**
```json
{
  "id": 1,
  "trial_id": 1,
  "content_type": "video",
  "data": {
    "file_path": "uploads/video_outputs/...",
    "status": "success",
    "metadata": {
      "trial_id": 1,
      "generated_at": "20231026_123456",
      "segments_count": 3,
      "assets_count": 8,
      "images_count": 8,
      "slides_count": 3
    },
    "intermediate_outputs": {
      "script": "uploads/video_outputs/.../outputs/step1_script.json",
      "assets": "uploads/video_outputs/.../outputs/step2_assets.json",
      "metadata": "uploads/video_outputs/.../metadata.json"
    }
  }
}
```

## Dependencies

### Python Requirements

```bash
# Core dependencies
google-generativeai>=0.8.0  # Gemini AI
Pillow>=10.0.0              # Image processing
requests>=2.31.0            # HTTP requests
rembg>=2.0.50              # Background removal (optional)

# Optional TTS
# Either configure ElevenLabs API key or:
pip install pyttsx3
```

### System Requirements

**ffmpeg** - Required for video composition:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Environment Variables

Required in `/backend/.env`:

```bash
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (for better TTS quality)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

## Usage

### 1. From Dashboard

1. Navigate to trial detail page
2. Ensure summary is generated first
3. Click "Generate" on the Video card
4. Wait for generation (may take 2-5 minutes)
5. Click "View Video" to watch the result

### 2. Viewing the Video

The video viewer provides:
- Full video playback with controls
- Download button for offline viewing
- Production metadata (segments, assets, slides)
- Access to intermediate outputs (JSON files)

### 3. Downloading Outputs

**Final Video:**
- Click "Download Video" button in VideoViewer
- Or access directly: `http://localhost:8000/uploads/video_outputs/trial_{id}/{timestamp}/final_video.mp4`

**Intermediate Outputs:**
- Script JSON: Contains narration and segment structure
- Assets JSON: Visual element specifications
- Metadata JSON: Complete production information

## Customization

### Adjusting Video Duration

In the generation endpoint (`/backend/app/routes/generation.py`):

```python
agent_input = {
    "simple_text": summary_text,
    "trial_id": trial_id,
    "duration": 90  # Change target duration in seconds
}
```

### Adding Background Music

```python
agent_input = {
    "simple_text": summary_text,
    "trial_id": trial_id,
    "music_path": "/path/to/background/music.mp3"  # Optional
}
```

### Modifying Prompts

Prompts are stored in `/backend/app/agents/video_agent/`:
- `video_transcript_generation_prompt.txt` - Script generation
- `video_asset_generation_prompt.txt` - Asset planning
- `video_prompt_prompts.txt` - Image prompt refinement
- `canvaa_prompts.txt` - Slide layout design

Edit these files to adjust the AI's behavior at each stage.

## Troubleshooting

### Video Generation Fails

1. **Check ffmpeg installation:**
   ```bash
   ffmpeg -version
   ```

2. **Check API keys:**
   ```bash
   cat backend/.env | grep GEMINI_API_KEY
   ```

3. **Check logs:**
   ```bash
   # Backend terminal will show detailed stage-by-stage progress
   ```

4. **Check error.json:**
   ```bash
   cat uploads/video_outputs/trial_{id}/{timestamp}/error.json
   ```

### Images Not Generating

- Pollinations AI may rate-limit requests
- Agent automatically retries with simplified prompts
- Check `step2_assets.json` for image specifications

### Background Removal Fails

- rembg is optional - videos will work without it
- To install: `pip install rembg`
- Requires ~1.7GB model download on first use

### TTS Not Working

Option 1 - Use ElevenLabs (recommended):
```bash
echo "ELEVENLABS_API_KEY=your_key" >> backend/.env
```

Option 2 - Use local TTS:
```bash
pip install pyttsx3
```

### Video Not Playing in Browser

- Ensure video was generated successfully (check file exists)
- Check browser console for CORS errors
- Verify `/uploads` is properly mounted in `main.py`
- Try different browser (Chrome/Firefox recommended)

## Performance Notes

**Generation Time:**
- Stage 1 (Script): ~10-15 seconds
- Stage 2 (Assets): ~5-10 seconds
- Stage 3 (Images): ~30-60 seconds (depends on image count)
- Stage 4 (Background Removal): ~10-20 seconds
- Stage 5 (Slides): ~5-10 seconds
- Stage 6 (Slide Creation): ~15-30 seconds
- Stage 7 (Video Composition): ~30-60 seconds

**Total:** Approximately 2-5 minutes per video

**Optimization Tips:**
- Use fewer segments for faster generation
- Reduce image count in prompts
- Skip background removal if not needed
- Use local TTS instead of ElevenLabs for faster synthesis

## Future Enhancements

Potential improvements:
- [ ] Real-time progress updates via WebSocket
- [ ] Queue system for multiple concurrent generations
- [ ] Custom narration voice selection
- [ ] Interactive video editing interface
- [ ] Thumbnail generation
- [ ] Video quality/resolution settings
- [ ] Batch video generation
- [ ] Video analytics and engagement tracking

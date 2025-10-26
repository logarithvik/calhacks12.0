# Video Generation - Quick Reference

## 🚀 Quick Start

### Prerequisites
```bash
# 1. Install ffmpeg
brew install ffmpeg  # macOS
# or: sudo apt-get install ffmpeg  # Linux

# 2. Run setup script
./setup_video_agent.sh

# 3. Add API key to backend/.env
GEMINI_API_KEY=your_actual_key_here
```

### Generate Your First Video
1. Upload a trial protocol PDF
2. Click "Generate" on Summary card → wait ~30 seconds
3. Click "Generate" on Video card → wait ~3 minutes
4. Click "View Video" to watch!

## 📁 Output Locations

```
uploads/video_outputs/trial_{id}/{timestamp}/
├── final_video.mp4          ← The video!
├── outputs/
│   ├── step1_script.json    ← Narration script
│   ├── step2_assets.json    ← Visual elements
│   └── step4_slides.json    ← Slide layouts
├── images/                  ← Generated images
├── slides/                  ← Slide PNGs
└── metadata.json           ← Production info
```

## 🎬 The 7-Stage Pipeline

| Stage | What It Does | Output | Time |
|-------|-------------|--------|------|
| 1️⃣ Script | Generate narration & segments | JSON | ~15s |
| 2️⃣ Assets | Plan visual elements | JSON | ~10s |
| 3️⃣ Images | Create images with AI | PNGs | ~45s |
| 4️⃣ Backgrounds | Remove backgrounds | PNGs | ~15s |
| 5️⃣ Layouts | Design slide composition | JSON | ~10s |
| 6️⃣ Slides | Create professional slides | PNGs | ~25s |
| 7️⃣ Compose | Assemble final video + TTS | MP4 | ~45s |

**Total: ~3 minutes per video**

## 🔧 Common Tasks

### Download Video
```bash
# From VideoViewer UI: Click "Download Video" button
# Or via URL:
http://localhost:8000/uploads/video_outputs/trial_1/.../final_video.mp4
```

### View Intermediate Outputs
- Navigate to VideoViewer page
- Scroll to "Production Details" section
- Click download links for JSON files

### Regenerate Video
- Click "Regenerate" button on Video card
- Creates new timestamped directory
- Preserves old versions

### Customize Duration
Edit `backend/app/routes/generation.py`:
```python
agent_input = {
    "simple_text": summary_text,
    "trial_id": trial_id,
    "duration": 120  # Change to desired seconds
}
```

## 🐛 Troubleshooting

### "Error generating video"
1. Check backend terminal for detailed logs
2. Look for `error.json` in output directory
3. Verify ffmpeg is installed: `ffmpeg -version`
4. Check API key in `.env`

### Images not generating
- Pollinations API may be slow/rate-limited
- Agent automatically retries with simpler prompts
- Check `step2_assets.json` for specifications

### Video won't play
- Verify file exists in uploads directory
- Check browser console for errors
- Try different browser (Chrome/Firefox)
- Ensure /uploads is mounted in main.py

### TTS fails
Option 1 - ElevenLabs (better quality):
```bash
echo "ELEVENLABS_API_KEY=your_key" >> backend/.env
```

Option 2 - Local (free):
```bash
pip install pyttsx3
```

## 📊 API Reference

### Generate Video
```http
POST /api/generate/video/{trial_id}
Authorization: Bearer {token}
```

### Get Video Data
```http
GET /api/generate/content/{content_id}/data
Authorization: Bearer {token}
```

### Response Structure
```json
{
  "file_path": "uploads/video_outputs/.../final_video.mp4",
  "status": "success",
  "metadata": {
    "segments_count": 3,
    "images_count": 8,
    "slides_count": 3
  },
  "intermediate_outputs": { ... }
}
```

## 🎨 Frontend Routes

| Route | Component | Purpose |
|-------|-----------|---------|
| `/trial/:id` | TrialDetail | Generate video |
| `/trial/:id/video/:contentId` | VideoViewer | Watch & download |

## ⚙️ Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| video_transcript_generation_prompt.txt | Script generation | `backend/app/agents/video_agent/` |
| video_asset_generation_prompt.txt | Asset planning | `backend/app/agents/video_agent/` |
| canvaa_prompts.txt | Slide layouts | `backend/app/agents/video_agent/` |

## 🔑 Environment Variables

Required:
```bash
GEMINI_API_KEY=your_gemini_api_key
```

Optional:
```bash
ELEVENLABS_API_KEY=your_elevenlabs_key  # Better TTS
GEMINI_MODEL_NAME=gemini-2.5-flash       # Model choice
GEMINI_TEMPERATURE=0.2                   # Creativity (0-1)
```

## 📈 Performance Tips

**Faster Generation:**
- Use fewer segments (edit prompts)
- Reduce image count per segment
- Skip background removal (comment out stage 4)
- Use local TTS instead of ElevenLabs

**Better Quality:**
- Use ElevenLabs for TTS
- Increase image resolution
- Add background music
- Adjust Gemini temperature for more creative scripts

## 🎯 Best Practices

1. **Always generate summary first** - Video needs text input
2. **Check trial status** - Wait for "completed" before viewing
3. **Monitor backend logs** - See real-time progress
4. **Preserve timestamps** - Old versions stay accessible
5. **Download videos** - For offline sharing/viewing

## 📚 Full Documentation

- Complete guide: `VIDEO_GENERATION_GUIDE.md`
- Integration summary: `VIDEO_INTEGRATION_SUMMARY.md`
- Setup script: `./setup_video_agent.sh`

## 💡 Pro Tips

- Videos are timestamped - you can compare different generations
- Intermediate JSON files are great for debugging
- Slide PNGs can be used independently (presentations!)
- Metadata shows exactly what was generated
- Error logs include full tracebacks for debugging

## 🆘 Getting Help

1. Check `VIDEO_GENERATION_GUIDE.md` for detailed docs
2. Review backend logs for error messages
3. Inspect `error.json` in output directory
4. Verify all dependencies with `./setup_video_agent.sh`
5. Check GitHub issues for known problems

---

**Happy video generating! 🎬✨**

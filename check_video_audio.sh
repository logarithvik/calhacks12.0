#!/bin/bash
# Video Audio Diagnostics Script
# Check if generated videos have audio tracks

echo "=================================="
echo "Video Audio Diagnostics"
echo "=================================="
echo ""

# Find the most recent video
VIDEO_DIR="uploads/video_outputs"

if [ ! -d "$VIDEO_DIR" ]; then
    echo "❌ No video outputs directory found at: $VIDEO_DIR"
    exit 1
fi

# Find most recent video
LATEST_VIDEO=$(find "$VIDEO_DIR" -name "final_video.mp4" -type f -print0 | xargs -0 ls -t | head -1)

if [ -z "$LATEST_VIDEO" ]; then
    echo "❌ No videos found in $VIDEO_DIR"
    exit 1
fi

echo "Analyzing: $LATEST_VIDEO"
echo ""

# Check if ffprobe is available
if ! command -v ffprobe &> /dev/null; then
    echo "❌ ffprobe not found (part of ffmpeg)"
    echo "Please install ffmpeg to use this diagnostic tool"
    exit 1
fi

echo "📊 Video Information:"
echo "-----------------------------------"

# Get video duration
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$LATEST_VIDEO" 2>/dev/null)
echo "Duration: ${DURATION}s"

# Get video codec
VIDEO_CODEC=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$LATEST_VIDEO" 2>/dev/null)
echo "Video codec: $VIDEO_CODEC"

# Get audio codec
AUDIO_CODEC=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$LATEST_VIDEO" 2>/dev/null)

if [ -z "$AUDIO_CODEC" ]; then
    echo "❌ Audio codec: NONE - Video has no audio track!"
    echo ""
    echo "This is the problem! The video was created without an audio stream."
    echo ""
    echo "Possible causes:"
    echo "1. TTS (Text-to-Speech) failed during generation"
    echo "2. Audio encoding failed during slide video creation"
    echo "3. Audio was lost during concatenation"
    echo ""
    echo "Solutions:"
    echo "1. Check that you have ElevenLabs API key set in backend/.env"
    echo "   OR install pyttsx3: pip install pyttsx3"
    echo "2. Regenerate the video with proper TTS configuration"
    echo "3. Check backend logs for TTS errors"
else
    echo "✅ Audio codec: $AUDIO_CODEC"
    
    # Get audio sample rate
    SAMPLE_RATE=$(ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1 "$LATEST_VIDEO" 2>/dev/null)
    echo "Sample rate: ${SAMPLE_RATE}Hz"
    
    # Get audio bitrate
    BITRATE=$(ffprobe -v error -select_streams a:0 -show_entries stream=bit_rate -of default=noprint_wrappers=1:nokey=1 "$LATEST_VIDEO" 2>/dev/null)
    BITRATE_KB=$((BITRATE / 1000))
    echo "Bitrate: ${BITRATE_KB}kbps"
    
    # Get audio channels
    CHANNELS=$(ffprobe -v error -select_streams a:0 -show_entries stream=channels -of default=noprint_wrappers=1:nokey=1 "$LATEST_VIDEO" 2>/dev/null)
    echo "Channels: $CHANNELS"
    
    echo ""
    echo "✅ Audio track exists!"
    echo ""
    echo "If you still can't hear audio in the browser:"
    echo "1. Check browser volume and video player controls"
    echo "2. Make sure the video player is not muted"
    echo "3. Try downloading the video and playing locally"
    echo "4. Check browser console for CORS errors"
fi

echo ""
echo "📋 Full Stream Information:"
echo "-----------------------------------"
ffprobe -v error -show_streams "$LATEST_VIDEO" 2>/dev/null | grep -E "(codec_name|codec_type|sample_rate|channels|bit_rate)"

echo ""
echo "=================================="

# Test audio extraction
echo ""
echo "🔊 Testing Audio Extraction:"
echo "-----------------------------------"

TEMP_AUDIO="/tmp/test_audio.wav"
ffmpeg -y -i "$LATEST_VIDEO" -vn -acodec pcm_s16le -ar 44100 -ac 2 "$TEMP_AUDIO" 2>&1 | grep -E "(Duration|Audio|Stream)"

if [ -f "$TEMP_AUDIO" ]; then
    AUDIO_SIZE=$(du -h "$TEMP_AUDIO" | cut -f1)
    echo ""
    if [ "$AUDIO_SIZE" = "0B" ] || [ "$AUDIO_SIZE" = "4.0K" ]; then
        echo "❌ Extracted audio is empty or silent"
        echo "The video has an audio track but it contains no sound"
    else
        echo "✅ Audio extracted successfully ($AUDIO_SIZE)"
        echo "You can play it with: afplay $TEMP_AUDIO"
    fi
    rm -f "$TEMP_AUDIO"
else
    echo "❌ Failed to extract audio"
fi

echo ""
echo "=================================="

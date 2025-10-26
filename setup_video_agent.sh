#!/bin/bash

# Video Agent Setup Script
# This script installs all dependencies needed for the video generation feature

set -e

echo "=================================="
echo "Video Agent Setup Script"
echo "=================================="
echo ""

# Check if running from correct directory
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# 1. Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt
echo "✅ Python dependencies installed"
echo ""

# 2. Check for ffmpeg
echo "🎬 Checking for ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg not found!"
    echo ""
    echo "Please install ffmpeg:"
    echo "  macOS:         brew install ffmpeg"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  Windows:       Download from https://ffmpeg.org/download.html"
    echo ""
    echo "After installing ffmpeg, run this script again."
    exit 1
else
    FFMPEG_VERSION=$(ffmpeg -version | head -n1)
    echo "✅ ffmpeg found: $FFMPEG_VERSION"
fi
echo ""

# 3. Check environment variables
echo "🔑 Checking environment variables..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit backend/.env and add your API keys:"
    echo "  - GEMINI_API_KEY (required)"
    echo "  - ELEVENLABS_API_KEY (optional, for better TTS)"
    echo ""
else
    if ! grep -q "GEMINI_API_KEY" .env || grep -q "GEMINI_API_KEY=your" .env; then
        echo "⚠️  GEMINI_API_KEY not configured in .env"
        echo "Please add your Gemini API key to backend/.env"
        echo ""
    else
        echo "✅ GEMINI_API_KEY found"
    fi
    
    if ! grep -q "ELEVENLABS_API_KEY" .env; then
        echo "ℹ️  ELEVENLABS_API_KEY not found (optional)"
        echo "For better text-to-speech quality, add your ElevenLabs API key"
        echo ""
    fi
fi

# 4. Create necessary directories
echo "📁 Creating output directories..."
mkdir -p uploads/video_outputs
mkdir -p uploads/generated
echo "✅ Directories created"
echo ""

# 5. Test imports
echo "🧪 Testing Python imports..."
python3 << EOF
try:
    import PIL
    print("✅ Pillow (PIL) imported successfully")
except ImportError:
    print("❌ Failed to import Pillow")
    exit(1)

try:
    import requests
    print("✅ requests imported successfully")
except ImportError:
    print("❌ Failed to import requests")
    exit(1)

try:
    import google.generativeai
    print("✅ google-generativeai imported successfully")
except ImportError:
    print("❌ Failed to import google-generativeai")
    exit(1)

try:
    from rembg import remove
    print("✅ rembg imported successfully (background removal available)")
except ImportError:
    print("⚠️  rembg not available (background removal will be skipped)")
    print("   To install: pip install rembg")

try:
    import pyttsx3
    print("✅ pyttsx3 imported successfully (local TTS available)")
except ImportError:
    print("⚠️  pyttsx3 not available (will need ElevenLabs API key for TTS)")
    print("   To install: pip install pyttsx3")
EOF

echo ""

# 6. Final checks
echo "🎯 Final setup verification..."
echo ""

ALL_OK=true

# Check ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg: OK"
else
    echo "❌ ffmpeg: NOT FOUND"
    ALL_OK=false
fi

# Check Python dependencies
if python3 -c "import PIL, requests, google.generativeai" 2>/dev/null; then
    echo "✅ Python dependencies: OK"
else
    echo "❌ Python dependencies: MISSING"
    ALL_OK=false
fi

# Check .env
if [ -f ".env" ] && grep -q "GEMINI_API_KEY" .env && ! grep -q "GEMINI_API_KEY=your" .env; then
    echo "✅ Environment variables: OK"
else
    echo "⚠️  Environment variables: NEEDS CONFIGURATION"
    ALL_OK=false
fi

# Check directories
if [ -d "uploads/video_outputs" ]; then
    echo "✅ Output directories: OK"
else
    echo "❌ Output directories: MISSING"
    ALL_OK=false
fi

echo ""
echo "=================================="

if [ "$ALL_OK" = true ]; then
    echo "✅ Setup complete! Video generation is ready to use."
    echo ""
    echo "Next steps:"
    echo "1. Start the backend: cd backend && uvicorn main:app --reload"
    echo "2. Start the frontend: cd frontend && npm run dev"
    echo "3. Generate a trial summary"
    echo "4. Click 'Generate' on the Video card"
    echo ""
    echo "For detailed usage instructions, see VIDEO_GENERATION_GUIDE.md"
else
    echo "⚠️  Setup incomplete. Please address the issues above."
    echo ""
    echo "For help, see VIDEO_GENERATION_GUIDE.md"
fi

echo "=================================="

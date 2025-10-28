# Backend - Clinical Trial Education Platform

FastAPI backend for distilling clinical trial protocols into educational content.

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Important:** The application requires several system-level dependencies for video generation:

- **ffmpeg**: Required for video composition and slide creation
  ```bash
  # macOS:
  brew install ffmpeg
  
  # Ubuntu/Debian:
  sudo apt-get install ffmpeg
  
  # Windows:
  # Download from https://ffmpeg.org/download.html
  ```

- **Python packages** (automatically installed with requirements.txt):
  - `rembg>=2.0.50` - Background removal for images
  - `onnxruntime>=1.16.0` - Runtime for rembg (ML model inference)
  - `pyttsx3>=2.90` - Local text-to-speech fallback
  - `Pillow>=10.0.0` - Image processing
  - `google-generativeai>=0.8.0` - Google Gemini AI integration

**Note on TTS**: For production video generation, configure the `ELEVENLABS_API_KEY` in your `.env` file for high-quality voice synthesis. `pyttsx3` provides a local fallback but with lower quality.

**Verify Installation:**
After installing dependencies, run the dependency checker:
```bash
python check_dependencies.py
```
This will verify all packages are properly installed and identify any missing system dependencies.

### 3. Setup PostgreSQL Database

```bash
# Install PostgreSQL (if not already installed)
# macOS:
brew install postgresql
brew services start postgresql

# Create database
createdb trial_edu_db

# Or use psql:
psql postgres
CREATE DATABASE trial_edu_db;
\q
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Run the Application

```bash
# From the backend directory
python main.py

# Or with uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

API documentation at http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── agents/           # AI agent modules
│   │   ├── distill_agent.py
│   │   ├── infographic_agent.py
│   │   └── video_agent.py
│   ├── models/           # Database models & schemas
│   │   ├── models.py
│   │   └── schemas.py
│   ├── routes/           # API endpoints
│   │   ├── auth.py
│   │   ├── trials.py
│   │   └── generation.py
│   ├── utils/            # Utility functions
│   │   ├── auth.py
│   │   └── file_utils.py
│   ├── config.py         # Configuration
│   └── database.py       # Database setup
├── uploads/              # Uploaded files & generated content
├── main.py               # Application entry point
└── requirements.txt      # Python dependencies
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user info

### Trials
- `GET /api/trials/` - List all trials
- `POST /api/trials/` - Create trial & upload protocol
- `GET /api/trials/{id}` - Get trial details
- `DELETE /api/trials/{id}` - Delete trial
- `GET /api/trials/{id}/protocol-text` - Get extracted text

### Generation (AI Agents)
- `POST /api/generate/summary/{trial_id}` - Generate summary
- `POST /api/generate/infographic/{trial_id}` - Generate infographic
- `POST /api/generate/video/{trial_id}` - Generate video
- `GET /api/generate/content/{content_id}/data` - Get content data

## Adding AI Agent Logic

The AI agents are in `app/agents/` and have placeholder implementations:

### distill_agent.py
- Extract structured data from protocol text
- Simplify medical jargon for patients
- **TODO**: Add LLM integration (OpenAI, Anthropic, etc.)

### infographic_agent.py
- Generate visual summaries
- **TODO**: Add image generation (Matplotlib, Pillow, AI services)

### video_agent.py
- Create educational videos with narration
- **TODO**: Add TTS and video generation (D-ID, MoviePy, etc.)

Each agent has a `run_agent(input_data)` function with detailed comments on implementation approaches.

## Testing

```bash
# Test endpoints with curl
curl http://localhost:8000/api/health

# Or use the interactive docs
open http://localhost:8000/docs
```

## Environment Variables

```
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/trial_edu_db

# Authentication
SECRET_KEY=your-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI API Keys (Required)
GEMINI_API_KEY=your-gemini-api-key

# Video Generation (Optional but recommended for high-quality TTS)
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Gemini Model Configuration (Optional)
GEMINI_MODEL_NAME=gemini-2.5-flash
GEMINI_TEMPERATURE=0.2
```

**Required API Keys:**
- `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `ELEVENLABS_API_KEY`: (Optional) Get from [ElevenLabs](https://elevenlabs.io/) for production-quality text-to-speech

**Note:** Without `ELEVENLABS_API_KEY`, the system will fall back to `pyttsx3` for local text-to-speech, which may have lower quality audio output.

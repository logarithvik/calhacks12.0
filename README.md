# Clinical Trial Education Platform

> **Hackathon MVP**: An open-source tool for clinical trial administrators to distill protocols into educational videos and infographics for patients.

## 🎯 Project Overview

### Problem
Clinical trial participants often lack clear, digestible information because:
- Protocols and consent documents are dense and technical
- Trial administrators lack bandwidth and communication tools
- Medical jargon is confusing for patients

### Solution
An AI-powered platform that:
- Distills clinical trial protocols into simple explanations
- Extracts key details (biological mechanism, side effects, schedule, visits)
- Converts information into videos and infographics for patients
- Allows administrators to review and edit generated content

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+

### 1. Clone the Repository

```bash
cd /Users/saketb/Documents/calhacks12.0
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb trial_edu_db

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run the backend
python main.py
```

Backend will run at: http://localhost:8000
API Docs at: http://localhost:8000/docs

### 3. Setup Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will run at: http://localhost:5173

### 4. Test the Application

1. Open http://localhost:5173
2. Register a new account
3. Upload a sample trial protocol (PDF or TXT)
4. Generate summary, infographic, and video
5. View the mock results

## 📁 Project Structure

```
calhacks12.0/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # AI agent modules ⭐
│   │   │   ├── distill_agent.py
│   │   │   ├── infographic_agent.py
│   │   │   └── video_agent.py
│   │   ├── models/         # Database models
│   │   ├── routes/         # API endpoints
│   │   ├── utils/          # Helper functions
│   │   ├── config.py
│   │   └── database.py
│   ├── uploads/            # Uploaded files
│   ├── main.py             # Entry point
│   └── requirements.txt
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   ├── services/       # API calls
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
└── README.md               # This file
```

## 🤖 AI Agent Modules

All agent files are in `backend/app/agents/` with **placeholder implementations**. Each has a `run_agent(input_data)` function with detailed TODOs.

### 1. Distillation Agent (`distill_agent.py`)

**Purpose**: Extract structured information from clinical trial protocols

**TODO - Add Agent Logic:**
```python
# Option 1: OpenAI GPT-4
from openai import OpenAI
client = OpenAI(api_key=settings.openai_api_key)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": f"Extract: {protocol_text}"}]
)

# Option 2: Anthropic Claude
from anthropic import Anthropic
client = Anthropic(api_key=settings.anthropic_api_key)

# Option 3: Local LLM with LangChain
from langchain.chains import create_extraction_chain
```

**Current Output** (mock):
- Study title, phase, duration
- Inclusion/exclusion criteria
- Side effects
- Visit schedule
- Biological mechanism
- Simple patient summary

### 2. Infographic Agent (`infographic_agent.py`)

**Purpose**: Generate visual summaries as images

**TODO - Add Agent Logic:**
```python
# Option 1: Matplotlib/Seaborn
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(11, 8.5))
# Create charts, timelines, text
plt.savefig(output_path)

# Option 2: Pillow for image composition
from PIL import Image, ImageDraw
img = Image.new('RGB', (1200, 1600), 'white')
# Add shapes, text, icons

# Option 3: AI Image Generation
# DALL-E, Stable Diffusion, etc.

# Option 4: External APIs
# Canva, Figma, Adobe Creative Cloud
```

**Current Output** (mock):
- File path to generated infographic
- Placeholder image location

### 3. Video Agent (`video_agent.py`)

**Purpose**: Create narrated educational videos

**TODO - Add Agent Logic:**
```python
# Option 1: AI Video Services
# D-ID, Synthesia, HeyGen APIs

# Option 2: MoviePy for programmatic video
from moviepy.editor import *
clips = [TextClip("Title"), ImageClip(img)]
final = concatenate_videoclips(clips)

# Option 3: Manim for animations
from manim import *

# Option 4: Combined approach
# - Script: GPT-4
# - TTS: Google Cloud TTS, ElevenLabs
# - Visuals: Stable Diffusion
# - Assembly: FFmpeg
```

**Current Output** (mock):
- Video script (scene by scene)
- File path to generated video
- Duration and format

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Create new account
- `POST /api/auth/login` - Login (returns JWT token)
- `GET /api/auth/me` - Get current user

### Trials
- `GET /api/trials/` - List all trials
- `POST /api/trials/` - Upload new protocol
- `GET /api/trials/{id}` - Get trial details
- `DELETE /api/trials/{id}` - Delete trial
- `GET /api/trials/{id}/protocol-text` - Extract text from PDF

### Generation (AI Agents)
- `POST /api/generate/summary/{trial_id}` - Generate summary
- `POST /api/generate/infographic/{trial_id}` - Generate infographic
- `POST /api/generate/video/{trial_id}` - Generate video
- `GET /api/generate/content/{content_id}/data` - Get content details

## 🧪 Local Testing

### Test with Demo Data

1. **Start both servers** (backend + frontend)

2. **Register/Login** at http://localhost:5173

3. **Upload a trial**:
   - Click "New Trial"
   - Enter title: "Phase II Cancer Treatment Study"
   - Upload a PDF or TXT file (any medical text)

4. **Generate Summary**:
   - Click on the trial
   - Click "Generate" under Summary
   - See mock extracted data

5. **Generate Infographic**:
   - After summary is generated
   - Click "Generate" under Infographic
   - See placeholder image

6. **Generate Video**:
   - After summary is generated
   - Click "Generate" under Video
   - See mock video script

### Test API Directly

```bash
# Health check
curl http://localhost:8000/api/health

# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"test123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -F "username=test" \
  -F "password=test123"
```

## 🔧 Adding Real AI Logic

### Step 1: Get API Keys

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Add to backend/.env
echo "OPENAI_API_KEY=sk-..." >> backend/.env
```

### Step 2: Install AI Libraries

```bash
cd backend
pip install openai anthropic langchain pillow matplotlib moviepy
```

### Step 3: Implement Agent Functions

Edit the `run_agent()` function in each agent file:

**Example for distill_agent.py:**

```python
from openai import OpenAI
from app.config import get_settings

def run_agent(input_data):
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    
    protocol_text = input_data["protocol_text"]
    
    # Create extraction prompt
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"""Extract the following from this clinical trial protocol:
            - Study title and phase
            - Duration
            - Inclusion/exclusion criteria
            - Side effects
            - Visit schedule
            
            Protocol: {protocol_text[:4000]}
            
            Return as JSON."""
        }]
    )
    
    # Parse and return
    return json.loads(response.choices[0].message.content)
```

## 🚀 Deployment

### Option 1: Docker Compose (Easiest)

```bash
# Create docker-compose.yml
docker-compose up -d
```

### Option 2: Individual Deployment

**Backend (Render, Railway, Fly.io):**
```bash
# Render
# 1. Connect GitHub repo
# 2. Set build command: pip install -r backend/requirements.txt
# 3. Set start command: cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
# 4. Add environment variables
```

**Frontend (Vercel, Netlify):**
```bash
# Vercel
cd frontend
vercel

# Netlify
npm run build
# Upload dist/ folder
```

### Option 3: Single Server

```bash
# Build frontend
cd frontend
npm run build

# Serve frontend from backend
# Update backend/main.py to serve static files from frontend/dist
```

## 📊 Database Schema

### Users
- id, email, username, hashed_password, created_at

### Trials
- id, title, protocol_file_path, status, user_id, created_at

### GeneratedContent
- id, trial_id, content_type, content_text, file_path, version, is_approved

## 🎨 Customization Ideas

1. **Add more extraction fields** in distill_agent
2. **Custom infographic templates** for different trial types
3. **Multiple video styles** (formal vs casual)
4. **PDF export** of summaries
5. **Email notifications** when content is ready
6. **Collaborative editing** of generated content
7. **Multi-language support**
8. **Voice clone** for narration
9. **Accessibility features** (screen reader optimized)

## 🐛 Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `pg_isready`
- Verify database exists: `psql -l | grep trial_edu`
- Check .env file has correct DATABASE_URL

### Frontend can't connect to backend
- Verify backend is running at http://localhost:8000
- Check VITE_API_URL in frontend/.env
- Check CORS settings in backend/main.py

### File upload fails
- Check uploads/ directory exists
- Verify file size is under 10MB
- Ensure PDF has extractable text

## 📝 License

MIT License - feel free to use for your hackathon!

## 🤝 Contributing

This is a hackathon MVP. Contributions welcome:
1. Fork the repo
2. Create a feature branch
3. Implement AI logic or new features
4. Submit a PR

## 🎓 Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Router](https://reactrouter.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic Claude](https://docs.anthropic.com/)
- [MoviePy Guide](https://zulko.github.io/moviepy/)

---

**Built for CalHacks 12.0** 🎉

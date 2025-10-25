# 🏗️ System Architecture

Visual guide to the Clinical Trial Education Platform architecture.

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │               React Frontend (Vite)                     │    │
│  │  • Login/Register Pages                                 │    │
│  │  • Dashboard (Trial List)                               │    │
│  │  • Trial Detail (Generate Content)                      │    │
│  │  • Tailwind CSS Styling                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            │ HTTP/REST API                       │
│                            ▼                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  Auth Routes     │  │  Trial Routes    │  │  Gen Routes  │  │
│  │  • /register     │  │  • /trials/      │  │  • /summary  │  │
│  │  • /login        │  │  • /trials/{id}  │  │  • /infograph│  │
│  │  • /me           │  │  • /upload       │  │  • /video    │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           │                     │                     │          │
│           └─────────────────────┼─────────────────────┘          │
│                                 │                                │
│                                 ▼                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Business Logic Layer                        │   │
│  │                                                           │   │
│  │  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ Distill Agent │  │ Infographic  │  │ Video Agent  │  │   │
│  │  │               │  │    Agent     │  │              │  │   │
│  │  │ Extracts      │  │ Generates    │  │ Creates      │  │   │
│  │  │ structured    │  │ visual       │  │ educational  │  │   │
│  │  │ data from     │  │ summaries    │  │ videos       │  │   │
│  │  │ protocols     │  │              │  │              │  │   │
│  │  │               │  │              │  │              │  │   │
│  │  │ TODO: Add     │  │ TODO: Add    │  │ TODO: Add    │  │   │
│  │  │ GPT-4/Claude  │  │ matplotlib/  │  │ D-ID/MoviePy │  │   │
│  │  └───────────────┘  │ Pillow/AI    │  └──────────────┘  │   │
│  │                     └──────────────┘                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                 │                                │
│                                 ▼                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              SQLAlchemy ORM Layer                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                 │                                │
└─────────────────────────────────┼────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                          │
│                                                                  │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ Users Table  │  │ Trials Table   │  │ Generated_Content│   │
│  │              │  │                │  │                  │   │
│  │ • id         │  │ • id           │  │ • id             │   │
│  │ • username   │  │ • title        │  │ • trial_id (FK)  │   │
│  │ • email      │  │ • file_path    │  │ • content_type   │   │
│  │ • password   │  │ • status       │  │ • content_text   │   │
│  │              │  │ • user_id (FK) │  │ • file_path      │   │
│  └──────────────┘  └────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       File System                                │
│                                                                  │
│  uploads/                                                        │
│  ├── trial_1_protocol.pdf         (uploaded protocols)          │
│  ├── infographic_1.png             (generated infographics)     │
│  ├── infographic_1_thumb.png       (thumbnails)                 │
│  ├── video_1.mp4                   (generated videos)           │
│  └── video_1_thumb.jpg             (video thumbnails)           │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Request Flow

### 1. User Registration
```
User → Frontend → POST /api/auth/register
                  → Backend validates
                  → Hash password
                  → Save to DB
                  ← Return user info
                ← Auto-login
```

### 2. Trial Upload
```
User → Upload Form → POST /api/trials/
                     → Multipart file upload
                     → Save PDF to uploads/
                     → Create trial record in DB
                     ← Return trial info
                   ← Show in dashboard
```

### 3. Generate Summary (AI Agent)
```
User → Click "Generate" → POST /api/generate/summary/{id}
                          → Get trial from DB
                          → Extract PDF text (PyPDF2)
                          → Call distill_agent.run_agent()
                            ┌─────────────────────────┐
                            │ TODO: Call GPT-4/Claude│
                            │ Extract:                │
                            │ • Study info            │
                            │ • Criteria              │
                            │ • Side effects          │
                            │ • Schedule              │
                            └─────────────────────────┘
                          ← Return structured data
                          → Save to generated_content table
                          ← Return content ID
                        ← Display summary
```

### 4. Generate Infographic
```
User → Click "Generate" → POST /api/generate/infographic/{id}
                          → Get summary from DB
                          → Call infographic_agent.run_agent()
                            ┌─────────────────────────┐
                            │ TODO: Generate image    │
                            │ • Matplotlib charts     │
                            │ • Pillow composition    │
                            │ • AI image gen          │
                            └─────────────────────────┘
                          → Save PNG to uploads/
                          → Save record to DB
                          ← Return file path
                        ← Display image
```

### 5. Generate Video
```
User → Click "Generate" → POST /api/generate/video/{id}
                          → Get summary from DB
                          → Call video_agent.run_agent()
                            ┌─────────────────────────┐
                            │ TODO: Create video      │
                            │ • Generate script       │
                            │ • TTS for narration     │
                            │ • Create scenes         │
                            │ • Render video          │
                            └─────────────────────────┘
                          → Save MP4 to uploads/
                          → Save record to DB
                          ← Return file path & script
                        ← Display video player
```

## 📦 Component Architecture

### Frontend Components

```
src/
├── App.jsx (Main Router)
│   ├── AuthProvider (Context)
│   ├── QueryClientProvider (React Query)
│   └── Routes
│       ├── /login → Login.jsx
│       ├── /register → Register.jsx
│       ├── /dashboard → Dashboard.jsx (Protected)
│       └── /trial/:id → TrialDetail.jsx (Protected)
│
├── components/
│   ├── Navbar.jsx
│   │   • User menu
│   │   • Logout
│   └── ProtectedRoute.jsx
│       • Auth check
│       • Redirect to login
│
├── pages/
│   ├── Login.jsx
│   │   • Form validation
│   │   • Call authAPI.login()
│   │   • Store JWT token
│   │
│   ├── Register.jsx
│   │   • Form validation
│   │   • Call authAPI.register()
│   │   • Auto-login
│   │
│   ├── Dashboard.jsx
│   │   • List trials
│   │   • Upload modal
│   │   • Delete trials
│   │   • Navigate to detail
│   │
│   └── TrialDetail.jsx
│       • Display trial info
│       • Generate buttons
│       • Show generated content
│       • Display summary/infographic/video
│
└── services/
    └── api.js
        • axios instance
        • JWT interceptors
        • authAPI
        • trialsAPI
        • generationAPI
```

### Backend Structure

```
app/
├── main.py (FastAPI App)
│   • CORS middleware
│   • Route includes
│   • Static file serving
│
├── config.py
│   • Environment variables
│   • Settings class
│
├── database.py
│   • SQLAlchemy engine
│   • Session factory
│   • get_db() dependency
│
├── models/
│   ├── models.py (SQLAlchemy)
│   │   • User model
│   │   • Trial model
│   │   • GeneratedContent model
│   │
│   └── schemas.py (Pydantic)
│       • Request/response models
│       • Validation schemas
│
├── routes/
│   ├── auth.py
│   │   • POST /register
│   │   • POST /login
│   │   • GET /me
│   │
│   ├── trials.py
│   │   • GET /trials/
│   │   • POST /trials/
│   │   • GET /trials/{id}
│   │   • DELETE /trials/{id}
│   │
│   └── generation.py
│       • POST /generate/summary/{trial_id}
│       • POST /generate/infographic/{trial_id}
│       • POST /generate/video/{trial_id}
│       • GET /content/{content_id}/data
│
├── agents/
│   ├── distill_agent.py
│   │   • run_agent(input_data)
│   │   • simplify_for_patients()
│   │
│   ├── infographic_agent.py
│   │   • run_agent(input_data)
│   │   • create_timeline_visual()
│   │
│   └── video_agent.py
│       • run_agent(input_data)
│       • generate_video_script()
│       • text_to_speech()
│
└── utils/
    ├── auth.py
    │   • verify_password()
    │   • get_password_hash()
    │   • create_access_token()
    │
    └── file_utils.py
        • save_upload_file()
        • extract_text_from_pdf()
```

## 🔐 Security Architecture

```
┌─────────────────────────────────────────┐
│           Security Layers                │
├─────────────────────────────────────────┤
│                                          │
│  1. Authentication (JWT)                 │
│     • Bearer token in headers            │
│     • Token expiration (30 min)          │
│     • Secure password hashing (bcrypt)   │
│                                          │
│  2. Authorization                        │
│     • User-specific resources            │
│     • Protected routes                   │
│     • Database foreign keys              │
│                                          │
│  3. Input Validation                     │
│     • Pydantic schemas                   │
│     • File type checking                 │
│     • Size limits                        │
│                                          │
│  4. CORS                                 │
│     • Whitelist frontend origins         │
│     • Credentials allowed                │
│                                          │
│  5. SQL Injection Protection             │
│     • SQLAlchemy ORM                     │
│     • Parameterized queries              │
│                                          │
└─────────────────────────────────────────┘
```

## 🚀 Deployment Architecture

### Development
```
┌────────────────┐        ┌────────────────┐
│   Frontend     │        │    Backend     │
│  localhost:    │  ←───→ │  localhost:    │
│     5173       │  HTTP  │     8000       │
└────────────────┘        └────────┬───────┘
                                   │
                                   ▼
                          ┌────────────────┐
                          │   PostgreSQL   │
                          │  localhost:    │
                          │     5432       │
                          └────────────────┘
```

### Production (Recommended)
```
┌─────────────────────────────────────────┐
│            Users / Browser               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Vercel (Frontend)                │
│  • Static site hosting                   │
│  • CDN distribution                      │
│  • HTTPS automatic                       │
└──────────────┬──────────────────────────┘
               │ API calls
               ▼
┌─────────────────────────────────────────┐
│        Render (Backend)                  │
│  • FastAPI instance                      │
│  • Auto-deploy from Git                  │
│  • HTTPS automatic                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Render PostgreSQL (Database)          │
│  • Managed database                      │
│  • Automatic backups                     │
│  • SSL connections                       │
└─────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Cloud Storage (Optional)              │
│  • AWS S3 for file uploads               │
│  • CloudFront CDN                        │
└─────────────────────────────────────────┘
```

## 📊 Data Flow Diagram

```
┌──────────┐
│   User   │
└────┬─────┘
     │
     │ 1. Upload Protocol
     ▼
┌──────────────────┐
│  Upload Handler  │
│  • Validate file │
│  • Save to disk  │
│  • Create record │
└────┬─────────────┘
     │
     │ 2. Store metadata
     ▼
┌──────────────────┐
│   Database       │
│  trials table    │
└────┬─────────────┘
     │
     │ 3. Trigger generation
     ▼
┌──────────────────┐
│ Distill Agent    │
│ • Extract text   │
│ • Parse with AI  │
│ • Structure data │
└────┬─────────────┘
     │
     │ 4. Save results
     ▼
┌──────────────────┐
│   Database       │
│ generated_       │
│ content table    │
└────┬─────────────┘
     │
     │ 5. Use for visuals
     ▼
┌──────────────────┐
│ Infographic      │
│ Agent            │
│ • Create charts  │
│ • Save image     │
└────┬─────────────┘
     │
     │ 6. Use for video
     ▼
┌──────────────────┐
│ Video Agent      │
│ • Generate script│
│ • Create video   │
│ • Save file      │
└────┬─────────────┘
     │
     │ 7. Display to user
     ▼
┌──────────────────┐
│  Frontend UI     │
│ • Show summary   │
│ • Show image     │
│ • Show video     │
└──────────────────┘
```

## 🎯 Technology Stack

### Frontend
```
React 18              → UI library
Vite 7                → Build tool (faster than CRA)
React Router 6        → Client-side routing
TanStack Query        → Server state management
Axios                 → HTTP client
Tailwind CSS 3        → Utility-first styling
Lucide React          → Icon library
```

### Backend
```
FastAPI 0.104         → Web framework
Python 3.11           → Language
SQLAlchemy 2.0        → ORM
PostgreSQL 15         → Database
Pydantic 2.5          → Data validation
python-jose           → JWT handling
passlib               → Password hashing
PyPDF2                → PDF parsing
```

### AI/ML (To be added)
```
OpenAI API            → Text extraction/summarization
Anthropic Claude      → Alternative LLM
LangChain             → LLM orchestration
Pillow/Matplotlib     → Image generation
MoviePy               → Video creation
ElevenLabs/Google TTS → Text-to-speech
```

### DevOps
```
Docker                → Containerization
Docker Compose        → Multi-container orchestration
PostgreSQL (Docker)   → Database
Nginx (optional)      → Reverse proxy
```

---

## 💡 Key Design Decisions

### Why FastAPI?
- Automatic API documentation (Swagger)
- Built-in validation with Pydantic
- Async support for scalability
- Type hints for better IDE support

### Why React + Vite?
- Fast development with HMR
- Modern build tooling
- Smaller bundle sizes
- Great DX (developer experience)

### Why PostgreSQL?
- Relational data (users ← trials ← content)
- ACID compliance
- Mature ecosystem
- Free tier availability

### Why Mock Implementations?
- Get working demo fast
- Test UI/UX before AI costs
- Easy to replace with real logic
- Clear separation of concerns

---

**This architecture is designed for rapid hackathon development while maintaining production-quality patterns!** 🚀

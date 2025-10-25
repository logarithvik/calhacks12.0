# ⚡ Quick Reference Guide

Your one-page reference for the Clinical Trial Education Platform.

## 🚀 Quick Start (3 Commands)

```bash
./setup.sh                         # Setup everything
cd backend && python main.py       # Start backend (Terminal 1)
cd frontend && npm run dev         # Start frontend (Terminal 2)
```

**Access**: http://localhost:5173

---

## 📁 Key Files to Edit

### Add AI Logic Here:

| File | What to Add | Line | Effort |
|------|-------------|------|--------|
| `backend/app/agents/distill_agent.py` | GPT-4/Claude extraction | ~53 | 2-4h |
| `backend/app/agents/infographic_agent.py` | Image generation | ~75 | 2-4h |
| `backend/app/agents/video_agent.py` | Video creation | ~89 | 3-6h |

### Configuration Files:

| File | Purpose |
|------|---------|
| `backend/.env` | API keys, database URL |
| `frontend/.env` | Backend API URL |
| `backend/requirements.txt` | Python packages |
| `frontend/package.json` | Node packages |

---

## 🔌 API Quick Reference

### Auth
```bash
# Register
POST /api/auth/register
Body: {"username":"test","email":"test@example.com","password":"test123"}

# Login
POST /api/auth/login
Form: username=test&password=test123
Returns: {"access_token":"...", "token_type":"bearer"}

# Get current user
GET /api/auth/me
Header: Authorization: Bearer <token>
```

### Trials
```bash
# Upload trial
POST /api/trials/
Form: title=MyTrial&protocol_file=@file.pdf
Header: Authorization: Bearer <token>

# List trials
GET /api/trials/
Header: Authorization: Bearer <token>

# Get trial details
GET /api/trials/1
Header: Authorization: Bearer <token>

# Delete trial
DELETE /api/trials/1
Header: Authorization: Bearer <token>
```

### Generation
```bash
# Generate summary
POST /api/generate/summary/1
Header: Authorization: Bearer <token>

# Generate infographic
POST /api/generate/infographic/1
Header: Authorization: Bearer <token>

# Generate video
POST /api/generate/video/1
Header: Authorization: Bearer <token>

# Get content details
GET /api/generate/content/1/data
Header: Authorization: Bearer <token>
```

---

## 💻 Common Commands

### Backend
```bash
# Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database
createdb trial_edu_db
dropdb trial_edu_db  # Reset if needed

# Run
python main.py
# or
uvicorn main:app --reload

# Install new package
pip install <package>
pip freeze > requirements.txt

# Deactivate venv
deactivate
```

### Frontend
```bash
# Setup
cd frontend
npm install

# Run
npm run dev

# Build
npm run build

# Preview build
npm run preview

# Install package
npm install <package>
```

### Database
```bash
# Connect
psql trial_edu_db

# Common queries
SELECT * FROM users;
SELECT * FROM trials;
SELECT * FROM generated_content;

# Reset
DROP TABLE generated_content, trials, users;
# Restart backend to recreate
```

### Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild
docker-compose build

# Stop
docker-compose down

# Reset everything
docker-compose down -v
docker-compose up -d --build
```

---

## 🐛 Debugging Checklist

### Backend won't start
- [ ] PostgreSQL running? `pg_isready`
- [ ] Database exists? `psql -l | grep trial_edu`
- [ ] Virtual env activated? `which python`
- [ ] Dependencies installed? `pip list`
- [ ] Correct Python version? `python --version` (need 3.8+)

### Frontend won't start
- [ ] Node installed? `node --version` (need 16+)
- [ ] Dependencies installed? `ls node_modules`
- [ ] Port 5173 available? `lsof -i :5173`

### Can't login
- [ ] User exists in database?
- [ ] Password correct?
- [ ] Token stored in localStorage?
- [ ] Backend /api/auth/login working? (check API docs)

### File upload fails
- [ ] File size < 10MB?
- [ ] File type is PDF or TXT?
- [ ] uploads/ directory exists?
- [ ] uploads/ has write permissions?

### Generation fails
- [ ] Summary generated first? (required for infographic/video)
- [ ] Trial file uploaded?
- [ ] Check backend logs for errors

---

## 🎨 Frontend Components

### Pages
```
/login           → Login.jsx
/register        → Register.jsx
/dashboard       → Dashboard.jsx (protected)
/trial/:id       → TrialDetail.jsx (protected)
```

### State Management
```javascript
// Auth context
const { user, login, logout, isAuthenticated } = useAuth();

// API calls
import { authAPI, trialsAPI, generationAPI } from './services/api';

// Example
const trials = await trialsAPI.getAll();
const summary = await generationAPI.generateSummary(trialId);
```

---

## 🔒 Environment Variables

### Backend (.env)
```bash
# Required
DATABASE_URL=postgresql://postgres:password@localhost:5432/trial_edu_db
SECRET_KEY=your-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional (add when implementing AI)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
```

---

## 📊 Database Schema

```sql
-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Trials
CREATE TABLE trials (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    protocol_file_path VARCHAR,
    original_filename VARCHAR,
    status VARCHAR DEFAULT 'uploaded',
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Generated Content
CREATE TABLE generated_content (
    id SERIAL PRIMARY KEY,
    trial_id INTEGER REFERENCES trials(id),
    content_type VARCHAR NOT NULL,
    content_text TEXT,
    file_path VARCHAR,
    file_url VARCHAR,
    is_approved BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🎯 Implementation Priority

### Phase 1: MVP Working (DONE ✅)
- [x] User auth
- [x] File upload
- [x] Mock AI pipeline
- [x] UI complete

### Phase 2: Add Real AI (2-6 hours)
1. Get API keys
2. Install AI libraries: `pip install openai anthropic`
3. Implement `distill_agent.py` → 2-4h
4. Implement `infographic_agent.py` → 2-4h
5. Implement `video_agent.py` → 3-6h

### Phase 3: Polish (1-2 hours)
- Error handling
- Loading states
- UI improvements
- Deploy to cloud

---

## 🚀 Deployment Shortcuts

### Render + Vercel (Free)
```bash
# Backend (Render)
# 1. Push to GitHub
git push origin main

# 2. Go to render.com → New Web Service
# 3. Connect repo, set:
#    - Root: backend
#    - Build: pip install -r requirements.txt
#    - Start: uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (Vercel)
cd frontend
vercel  # Follow prompts
```

### Docker (Local/VPS)
```bash
docker-compose up -d
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `ARCHITECTURE.md` | System design |
| `TESTING.md` | Testing guide |
| `DEPLOYMENT.md` | Deployment options |
| `PROJECT_SUMMARY.md` | Complete summary |
| `QUICK_REFERENCE.md` | This file |

---

## 💡 Pro Tips

1. **Test mock data first** - Ensure UI works before adding AI
2. **Use API docs** - http://localhost:8000/docs is your friend
3. **Check browser console** - Most frontend issues show there
4. **Monitor backend logs** - See request/response in terminal
5. **Git commit often** - Save your progress
6. **Start simple** - Get one feature working before moving on

---

## 🆘 Need Help?

### Check These First:
1. Is PostgreSQL running?
2. Is backend running on port 8000?
3. Is frontend running on port 5173?
4. Are both .env files configured?
5. Did you activate the venv?

### Common Errors:
| Error | Solution |
|-------|----------|
| "Database does not exist" | Run `createdb trial_edu_db` |
| "Port already in use" | Kill process: `lsof -ti:8000 \| xargs kill -9` |
| "Module not found" | Reinstall: `pip install -r requirements.txt` |
| "Can't connect to backend" | Check VITE_API_URL in frontend/.env |
| "Unauthorized" | Login again, check token in localStorage |

---

## ⚡ Speed Run (Get Running in 5 Minutes)

```bash
# 1. Setup (1 min)
cd /Users/saketb/Documents/calhacks12.0
./setup.sh

# 2. Start backend (1 min)
cd backend
source venv/bin/activate
python main.py &

# 3. Start frontend (1 min)  
cd ../frontend
npm run dev &

# 4. Test (2 min)
# Open http://localhost:5173
# Register account
# Upload sample trial
# Generate summary
# View results

# DONE! ✅
```

---

**Bookmark this page for quick reference during your hackathon!** 🚀

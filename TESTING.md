# 🧪 Local Testing Guide

Complete guide to testing your Clinical Trial Education Platform locally.

## Prerequisites

- Backend running at http://localhost:8000
- Frontend running at http://localhost:5173
- PostgreSQL database created

## Quick Setup

```bash
# From project root
./setup.sh

# Then start backend
cd backend
source venv/bin/activate
python main.py

# In new terminal, start frontend
cd frontend
npm run dev
```

## Test Flow

### 1. Test User Registration

1. Go to http://localhost:5173
2. You'll be redirected to login page
3. Click "Register here"
4. Fill in:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `test123`
   - Confirm Password: `test123`
5. Click "Register"
6. Should automatically log you in and redirect to dashboard

**Expected Result**: Empty dashboard with "No trials yet" message

### 2. Test Trial Upload

1. On dashboard, click "New Trial" button
2. Fill in:
   - Trial Title: `Phase II Cancer Treatment Study`
   - Upload a file (use sample below)
3. Click "Upload"

**Sample Test File**: Create a file named `sample_protocol.txt`:

```
Clinical Trial Protocol

Title: Phase II Study of Novel Immunotherapy in Advanced Melanoma
Phase: Phase II
Duration: 18 months

Study Design:
This is a randomized, double-blind, placebo-controlled study evaluating the efficacy and safety of investigational drug XYZ-123 in patients with advanced melanoma.

Inclusion Criteria:
- Age 18-75 years
- Histologically confirmed melanoma
- ECOG performance status 0-1
- Adequate organ function

Exclusion Criteria:
- Prior treatment with similar immunotherapy agents
- Active autoimmune disease
- Pregnancy or breastfeeding
- Uncontrolled brain metastases

Treatment Plan:
Patients will receive XYZ-123 200mg IV every 3 weeks for up to 12 cycles.

Visit Schedule:
- Screening: Day -14 to Day -1
- Baseline: Day 0
- Treatment visits: Every 3 weeks
- End of treatment: Week 36
- Follow-up: Every 12 weeks for 2 years

Expected Side Effects:
- Fatigue (common)
- Nausea
- Skin reactions at infusion site
- Immune-related adverse events (rare)

Primary Endpoint:
Overall response rate at 12 weeks

Secondary Endpoints:
- Progression-free survival
- Overall survival
- Safety and tolerability
```

**Expected Result**: Trial appears in dashboard with "uploaded" status

### 3. Test Summary Generation

1. Click "View" on the uploaded trial
2. On trial detail page, click "Generate" under Summary card
3. Wait for processing (should be fast with mock data)

**Expected Result**:
- Summary card shows "Generated" with green checkmark
- Summary section appears below with:
  - Patient-friendly text
  - Structured data (study info, criteria, side effects, etc.)
  
**Mock Data Should Include**:
- Study title and phase
- Duration (12 months)
- Inclusion/exclusion criteria (3+ items each)
- Visit schedule (4+ visits)
- Side effects list
- Biological mechanism explanation

### 4. Test Infographic Generation

1. After summary is generated, click "Generate" under Infographic
2. Wait for processing

**Expected Result**:
- Infographic card shows "Generated"
- Infographic section appears with placeholder
- Shows file path (e.g., `uploads/infographic_1.png`)

### 5. Test Video Generation

1. After summary is generated, click "Generate" under Video
2. Wait for processing

**Expected Result**:
- Video card shows "Generated"
- Video section appears with placeholder
- Shows mock video script in content details

### 6. Test Regeneration

1. Click "Regenerate" on any generated content
2. Should update version number

**Expected Result**: Content updates, version increments

### 7. Test Navigation

1. Click "Back to Dashboard"
2. Should see the trial in the list
3. Trial should show generated content badges (summary, infographic, video)

### 8. Test Trial Deletion

1. On dashboard, click trash icon on a trial
2. Confirm deletion
3. Trial disappears from list

**Expected Result**: Trial removed from database

## API Testing with curl

### Register User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "apitest",
    "email": "api@test.com",
    "password": "test123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -F "username=apitest" \
  -F "password=test123"
```

Save the returned token:
```bash
TOKEN="<your-token-here>"
```

### Upload Trial

```bash
curl -X POST http://localhost:8000/api/trials/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=API Test Trial" \
  -F "protocol_file=@sample_protocol.txt"
```

### Generate Summary

```bash
curl -X POST http://localhost:8000/api/generate/summary/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Get Trial Details

```bash
curl http://localhost:8000/api/trials/1 \
  -H "Authorization: Bearer $TOKEN"
```

## Testing with Interactive API Docs

1. Go to http://localhost:8000/docs
2. You'll see Swagger UI with all endpoints
3. Click "Authorize" button
4. Login to get token
5. Use the token to test other endpoints

## Common Issues

### 1. "Trial not found" Error
- **Cause**: Trial ID doesn't exist or belongs to different user
- **Fix**: Check trial ID, verify you're logged in as correct user

### 2. "Please generate summary first"
- **Cause**: Trying to generate infographic/video without summary
- **Fix**: Generate summary first (it's required)

### 3. Database Connection Error
- **Cause**: PostgreSQL not running or wrong credentials
- **Fix**: 
  ```bash
  # Check PostgreSQL is running
  pg_isready
  
  # Start PostgreSQL (macOS)
  brew services start postgresql
  ```

### 4. File Upload Fails
- **Cause**: File too large or wrong format
- **Fix**: Use PDF or TXT files under 10MB

### 5. Frontend Can't Connect to Backend
- **Cause**: Backend not running or wrong API URL
- **Fix**: 
  - Check backend is running: `curl http://localhost:8000/api/health`
  - Verify `VITE_API_URL` in frontend/.env

## Performance Testing

### Test with Multiple Trials

```bash
# Upload 5 trials
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/trials/ \
    -H "Authorization: Bearer $TOKEN" \
    -F "title=Test Trial $i" \
    -F "protocol_file=@sample_protocol.txt"
done
```

### Test Concurrent Generation

```bash
# Generate summaries for multiple trials simultaneously
curl -X POST http://localhost:8000/api/generate/summary/1 -H "Authorization: Bearer $TOKEN" &
curl -X POST http://localhost:8000/api/generate/summary/2 -H "Authorization: Bearer $TOKEN" &
curl -X POST http://localhost:8000/api/generate/summary/3 -H "Authorization: Bearer $TOKEN" &
wait
```

## Next Steps: Adding Real AI

Once testing is complete, implement real AI logic:

1. **Add API Keys**:
   ```bash
   echo "OPENAI_API_KEY=sk-..." >> backend/.env
   ```

2. **Install AI Libraries**:
   ```bash
   cd backend
   source venv/bin/activate
   pip install openai anthropic langchain
   ```

3. **Implement Agents**:
   - Edit `backend/app/agents/distill_agent.py`
   - Edit `backend/app/agents/infographic_agent.py`
   - Edit `backend/app/agents/video_agent.py`

4. **Test with Real Protocol**:
   - Download a real clinical trial protocol PDF
   - Upload and generate
   - Verify extraction quality

## Debugging Tips

### Check Backend Logs
```bash
# Backend should print requests
# Look for errors or stack traces
```

### Check Browser Console
```bash
# Open browser DevTools (F12)
# Check Console tab for errors
# Check Network tab for failed requests
```

### Check Database
```bash
psql trial_edu_db

# List users
SELECT * FROM users;

# List trials
SELECT * FROM trials;

# List generated content
SELECT * FROM generated_content;
```

### Reset Database
```bash
# Drop and recreate
dropdb trial_edu_db
createdb trial_edu_db

# Restart backend to recreate tables
```

## Success Criteria

✅ Can register and login  
✅ Can upload trial protocol  
✅ Can generate summary with mock data  
✅ Can generate infographic (placeholder)  
✅ Can generate video (placeholder)  
✅ Can view all generated content  
✅ Can delete trials  
✅ Data persists across page refreshes  

---

**Ready for the hackathon!** 🎉

When you implement real AI logic, repeat these tests to verify everything still works.

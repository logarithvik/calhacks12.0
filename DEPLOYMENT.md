# 🚀 Deployment Guide

Quick deployment options for your hackathon demo.

## Option 1: Docker Compose (Fastest for Demo)

Perfect for running everything locally or on a single server.

```bash
# Make sure Docker and Docker Compose are installed
docker --version
docker-compose --version

# Start everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

Access at:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Option 2: Cloud Deployment (Production-Ready)

### Backend Deployment

#### Render.com (Recommended)

1. **Prepare your repo**:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy on Render**:
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Configure:
     - **Name**: `trial-edu-backend`
     - **Root Directory**: `backend`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`
     - **Instance Type**: Free

3. **Add Environment Variables**:
   ```
   DATABASE_URL=<Render-PostgreSQL-URL>
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

4. **Add PostgreSQL**:
   - In Render dashboard, create "New +" → "PostgreSQL"
   - Copy the connection string
   - Add to backend environment variables

#### Railway.app Alternative

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd backend
railway init

# Add PostgreSQL
railway add

# Deploy
railway up

# Open
railway open
```

### Frontend Deployment

#### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Follow prompts
# Set environment variable: VITE_API_URL=https://your-backend.onrender.com
```

Or use Vercel Dashboard:
1. Go to https://vercel.com
2. Import GitHub repo
3. Set root directory to `frontend`
4. Add environment variable: `VITE_API_URL`
5. Deploy

#### Netlify Alternative

```bash
# Build frontend
cd frontend
npm run build

# Deploy
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

## Option 3: Heroku

### Backend

```bash
cd backend

# Create Heroku app
heroku create trial-edu-backend

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key

# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Frontend

```bash
cd frontend

# Create Heroku app
heroku create trial-edu-frontend

# Add buildpack
heroku buildpacks:set heroku/nodejs

# Create static.json for serving
echo '{"root": "dist/"}' > static.json

# Add build script to package.json
# "heroku-postbuild": "npm run build"

# Deploy
git push heroku main
```

## Option 4: Single VPS (DigitalOcean, Linode, etc.)

### Setup Server

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3-pip python3-venv nodejs npm postgresql nginx

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### Deploy Backend

```bash
# Clone repo
git clone https://github.com/yourusername/calhacks12.0.git
cd calhacks12.0/backend

# Setup Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup PostgreSQL
sudo -u postgres createdb trial_edu_db

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Run with supervisor or systemd
# Create systemd service file
sudo nano /etc/systemd/system/trial-edu.service
```

**Service file content**:
```ini
[Unit]
Description=Clinical Trial Education Platform
After=network.target

[Service]
User=www-data
WorkingDirectory=/root/calhacks12.0/backend
Environment="PATH=/root/calhacks12.0/backend/venv/bin"
ExecStart=/root/calhacks12.0/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl start trial-edu
sudo systemctl enable trial-edu
```

### Deploy Frontend

```bash
cd ../frontend

# Build
npm install
npm run build

# Copy to nginx
sudo cp -r dist/* /var/www/html/

# Configure nginx
sudo nano /etc/nginx/sites-available/trial-edu
```

**Nginx config**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /uploads {
        proxy_pass http://localhost:8000;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/trial-edu /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## Environment Variables

### Backend (.env)

```bash
# Required
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=generate-a-secure-random-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional (for AI features)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Frontend (.env)

```bash
VITE_API_URL=https://your-backend-url.com
```

## Security Checklist

- [ ] Change SECRET_KEY to a secure random string
- [ ] Use HTTPS for production
- [ ] Set strong PostgreSQL password
- [ ] Enable CORS only for your frontend domain
- [ ] Don't commit .env files to Git
- [ ] Use environment variables for all secrets
- [ ] Set up database backups
- [ ] Rate limit API endpoints
- [ ] Validate file uploads (size, type)
- [ ] Sanitize user inputs

## Monitoring

### Basic Health Checks

```bash
# Backend health
curl https://your-backend.com/api/health

# Check database connection
psql $DATABASE_URL -c "SELECT 1;"
```

### Logs

```bash
# Docker Compose
docker-compose logs -f backend
docker-compose logs -f frontend

# Systemd
sudo journalctl -u trial-edu -f

# Heroku
heroku logs --tail
```

## Scaling Considerations

### For High Traffic

1. **Database**:
   - Use connection pooling (PgBouncer)
   - Add read replicas
   - Use managed database service

2. **Backend**:
   - Run multiple instances behind load balancer
   - Use Redis for caching
   - Queue long-running tasks (Celery)

3. **File Storage**:
   - Use S3 or cloud storage
   - Serve static files via CDN

4. **Frontend**:
   - Use CDN (Cloudflare, CloudFront)
   - Enable caching
   - Optimize bundle size

## Cost Estimates (Monthly)

### Free Tier (Demo)
- Render: Free (backend)
- Vercel: Free (frontend)
- Render PostgreSQL: Free
- **Total: $0**

### Production (Small Scale)
- Render Web Service: $7
- Render PostgreSQL: $7
- Vercel Pro: $20 (optional)
- **Total: $14-34/month**

### Production (Growing)
- DigitalOcean Droplet: $12
- Managed PostgreSQL: $15
- CDN: $10
- **Total: $37/month**

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Verify database connection
echo $DATABASE_URL
```

### Database connection fails
```bash
# Check PostgreSQL is running
pg_isready -h localhost

# Test connection
psql $DATABASE_URL -c "SELECT version();"
```

### Frontend can't reach backend
- Check CORS settings in backend
- Verify VITE_API_URL is correct
- Check if backend is running

### File uploads fail in production
- Check upload directory permissions
- Verify file size limits
- Use cloud storage (S3) for production

## Quick Deploy Commands

```bash
# Render
git push origin main  # Auto-deploys if connected

# Vercel
vercel --prod

# Heroku
git push heroku main

# Docker
docker-compose up -d --build
```

## Post-Deployment Testing

1. ✅ Register new user
2. ✅ Upload trial protocol
3. ✅ Generate summary
4. ✅ Generate infographic
5. ✅ Generate video
6. ✅ Check database persistence
7. ✅ Test on mobile device
8. ✅ Verify HTTPS works
9. ✅ Check API docs accessible
10. ✅ Test error handling

---

**Choose the deployment method that fits your hackathon timeline!**

For quick demo: Use Docker Compose  
For professional demo: Use Render + Vercel  
For full control: Use VPS with nginx

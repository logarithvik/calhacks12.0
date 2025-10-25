#!/bin/bash

# Clinical Trial Education Platform - Setup Script
# This script sets up the entire project for local development

echo "🚀 Setting up Clinical Trial Education Platform..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL not found. Please install PostgreSQL${NC}"
    echo "   macOS: brew install postgresql"
    echo "   Ubuntu: sudo apt-get install postgresql"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL found${NC}"

echo ""
echo "🗄️  Setting up database..."

# Create database if it doesn't exist
if ! psql -lqt | cut -d \| -f 1 | grep -qw trial_edu_db; then
    createdb trial_edu_db
    echo -e "${GREEN}✓ Database 'trial_edu_db' created${NC}"
else
    echo -e "${YELLOW}⚠️  Database 'trial_edu_db' already exists${NC}"
fi

echo ""
echo "🐍 Setting up backend..."

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit backend/.env with your configuration${NC}"
fi

cd ..

echo ""
echo "⚛️  Setting up frontend..."

cd frontend

# Install dependencies
npm install > /dev/null 2>&1
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

cd ..

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open your browser to http://localhost:5173"
echo ""
echo "4. Register an account and upload a trial protocol!"
echo ""
echo "🤖 To add AI functionality:"
echo "   - Add your API keys to backend/.env"
echo "   - Edit the agent files in backend/app/agents/"
echo "   - See README.md for detailed instructions"
echo ""

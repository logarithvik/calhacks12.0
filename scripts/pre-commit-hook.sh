#!/bin/bash
# Git pre-commit hook to prevent committing secrets
# Place this in .git/hooks/pre-commit and make it executable

echo "🔍 Checking for potential secrets in staged files..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env files are being committed (except .env.example)
ENV_FILES=$(git diff --cached --name-only | grep -E "\.env$|\.env\.[^e]" || true)
if [ ! -z "$ENV_FILES" ]; then
    echo -e "${RED}❌ ERROR: .env file(s) detected in commit:${NC}"
    echo "$ENV_FILES"
    echo -e "${YELLOW}These files should not be committed. Add them to .gitignore.${NC}"
    exit 1
fi

# Check for potential hardcoded API keys in Python files
PYTHON_SECRETS=$(git diff --cached -U0 | grep -E "^\+.*['\"]?[A-Z_]*API[_-]?KEY['\"]?\s*=\s*['\"][a-zA-Z0-9]{20,}" || true)
if [ ! -z "$PYTHON_SECRETS" ]; then
    echo -e "${RED}❌ ERROR: Potential hardcoded API key detected:${NC}"
    echo "$PYTHON_SECRETS"
    echo -e "${YELLOW}Use environment variables instead of hardcoded secrets.${NC}"
    exit 1
fi

# Check for potential hardcoded secrets in JavaScript files
JS_SECRETS=$(git diff --cached -U0 | grep -E "^\+.*(apiKey|secretKey|password)\s*[:=]\s*['\"][a-zA-Z0-9]{20,}" || true)
if [ ! -z "$JS_SECRETS" ]; then
    echo -e "${RED}❌ ERROR: Potential hardcoded secret detected in JS/JSX:${NC}"
    echo "$JS_SECRETS"
    echo -e "${YELLOW}Use environment variables instead of hardcoded secrets.${NC}"
    exit 1
fi

# Check for common secret patterns
SECRET_PATTERNS=$(git diff --cached -U0 | grep -E "^\+.*(sk-[a-zA-Z0-9]{40,}|AIza[a-zA-Z0-9]{35})" || true)
if [ ! -z "$SECRET_PATTERNS" ]; then
    echo -e "${RED}❌ ERROR: Detected pattern matching known secret formats:${NC}"
    echo "$SECRET_PATTERNS"
    echo -e "${YELLOW}This looks like an API key. Please remove it.${NC}"
    exit 1
fi

# Check for database connection strings with passwords
DB_SECRETS=$(git diff --cached -U0 | grep -E "^\+.*(postgresql|mysql|mongodb)://[^:]+:[^@]+@" || true)
if [ ! -z "$DB_SECRETS" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Database connection string with password detected:${NC}"
    echo "$DB_SECRETS"
    echo -e "${YELLOW}Consider using environment variables for database credentials.${NC}"
    # Not failing here, just warning
fi

echo -e "${GREEN}✅ No obvious secrets detected. Proceeding with commit.${NC}"
exit 0

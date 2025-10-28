# Security Guidelines

This document outlines security best practices for the Clinical Trial Education Platform.

## 🔒 Environment Variables & Secrets

### Protected Files

The following files contain sensitive information and are **automatically excluded** from git:

- `.env` - Main environment configuration file
- `.env.*` - Any environment-specific files (e.g., `.env.local`, `.env.production`)
- `*secret*` - Any files with "secret" in the name
- `*key*.txt`, `*token*.txt` - Files containing keys or tokens
- `*.pem`, `*.key`, `*.cer`, `*.crt` - Certificate and key files

### Safe to Commit

Only the following example files should be committed:
- `.env.example` - Template file with dummy values

### API Keys & Secrets

**Never commit:**
- ❌ Actual API keys
- ❌ Database passwords
- ❌ Secret keys
- ❌ Access tokens
- ❌ Private keys or certificates

**Always use environment variables:**
```python
# ✅ GOOD - Using environment variables
api_key = os.getenv("GEMINI_API_KEY")

# ❌ BAD - Hardcoded secret
api_key = "AIzaSyC1234567890abcdef"
```

## 🛡️ Current Security Measures

### 1. Environment Configuration

The application uses `pydantic-settings` to load configuration from environment variables:

```python
# backend/app/config.py
class Settings(BaseSettings):
    gemini_api_key: str = ""  # Loaded from .env
    secret_key: str = "..."   # Default (should be changed in .env)
    
    class Config:
        env_file = ".env"
```

### 2. Git Protection

Multiple layers of `.gitignore` files protect sensitive data:
- Root `.gitignore` - General Python/Node patterns
- `backend/.gitignore` - Backend-specific exclusions
- `frontend/.gitignore` - Frontend-specific exclusions

### 3. Configuration Template

The `.env.example` file provides a template without real secrets:
```bash
# Template (safe to commit)
GEMINI_API_KEY=your-gemini-api-key-here

# Real file (never committed)
GEMINI_API_KEY=AIzaSyC1234567890abcdef
```

## ✅ Pre-Commit Checklist

Before committing code, verify:

1. **No `.env` files in staged changes**
   ```bash
   git status | grep .env
   # Should only show .env.example (if modified)
   ```

2. **No hardcoded secrets in code**
   ```bash
   # Check for potential hardcoded keys
   git diff --cached | grep -i "api[_-]key.*=.*['\"][a-zA-Z0-9]"
   ```

3. **Review changes carefully**
   ```bash
   git diff --cached
   ```

## 🚨 What To Do If Secrets Are Committed

If you accidentally commit secrets to git:

### 1. Immediately Rotate the Compromised Secrets
- Generate new API keys
- Change passwords
- Update tokens

### 2. Remove from Git History
```bash
# For the most recent commit
git reset HEAD~1
git add .
git commit -m "Your message"

# For older commits (use with caution)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/file" \
  --prune-empty --tag-name-filter cat -- --all
```

### 3. Force Push (if already pushed)
```bash
git push --force-with-lease origin main
```

### 4. Notify Team
- Inform all team members
- Update documentation
- Review access logs for unauthorized usage

## 📋 Required API Keys

### Production Environment

Set these in your `.env` file:

```bash
# Required
GEMINI_API_KEY=your-actual-key

# Database (production)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Security
SECRET_KEY=generate-a-strong-random-secret-key

# Optional (recommended)
ELEVENLABS_API_KEY=your-actual-key
```

### Obtaining API Keys

1. **Google Gemini API**
   - Visit: https://makersuite.google.com/app/apikey
   - Create or select a project
   - Generate API key
   - Copy to `.env` file

2. **ElevenLabs API** (Optional)
   - Visit: https://elevenlabs.io/
   - Sign up for an account
   - Navigate to Profile → API Keys
   - Copy to `.env` file

## 🔍 Security Scanning

### Manual Check
```bash
# Check for potential secrets in codebase
cd /Users/saketb/Documents/calhacks12.0
git ls-files | xargs grep -l "api[_-]key.*=.*['\"][a-zA-Z0-9]{20,}"
```

### Recommended Tools
- [git-secrets](https://github.com/awslabs/git-secrets) - Prevents committing secrets
- [truffleHog](https://github.com/trufflesecurity/trufflehog) - Finds secrets in git history
- [gitleaks](https://github.com/gitleaks/gitleaks) - SAST tool for detecting secrets

## 📚 Additional Resources

- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub's Security Best Practices](https://docs.github.com/en/code-security/getting-started/securing-your-repository)
- [12-Factor App Config](https://12factor.net/config)

## 🤝 Contributing

When contributing to this project:

1. **Never commit** `.env` files with real secrets
2. **Always use** `.env.example` for sharing configuration templates
3. **Keep secrets** in environment variables, never in code
4. **Review changes** carefully before committing
5. **Report any** accidental secret exposure immediately

---

**Last Updated:** October 27, 2025

If you find a security vulnerability, please email the maintainers privately rather than opening a public issue.

# Environment Setup Guide

**Using .env file for API Key** ✅

---

## ✅ Current Setup

You've correctly created a `.env` file with your API key!

**Location**: `/home/peter/DEV/formulafinance/reportpf/.env`

**Contents**:
```bash
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

---

## 🚀 How to Start the Server

### Option 1: Use the Start Script (Easiest)

```bash
./start_with_env.sh
```

This script:
- ✅ Loads `.env` automatically
- ✅ Activates virtual environment
- ✅ Starts the server

### Option 2: Manual Start

```bash
# 1. Load .env file
export $(cat .env | grep -v '^#' | xargs)

# 2. Activate venv
source venv/bin/activate

# 3. Start server
python api_server.py
```

### Option 3: Use source command

```bash
# Load .env
source .env

# Or use set -a
set -a
source .env
set +a

# Then start
python api_server.py
```

---

## 🔒 Security

### ✅ What We Did

1. **Created `.env` file** - Stores API key separately
2. **Added to `.gitignore`** - Won't be committed to git
3. **Created `.env.example`** - Template for others (no real key)

### ⚠️ Important

**Never commit `.env` to git!**

Your `.gitignore` now includes:
```
.env
```

This keeps your API key safe.

---

## 📁 File Structure

```
reportpf/
├── .env                    ← Your actual API key (NOT in git)
├── .env.example            ← Template (safe to commit)
├── .gitignore              ← Includes .env
├── start_with_env.sh       ← Easy start script
└── api_server.py           ← The server
```

---

## 🔄 Updating the API Key

If you need to change the API key:

```bash
# Edit .env file
nano .env

# Or
echo "ANTHROPIC_API_KEY=new-key-here" > .env

# Restart server
./start_with_env.sh
```

---

## 🧪 Verify Setup

```bash
# Check .env exists
ls -la .env

# Check it's in .gitignore
grep .env .gitignore

# Check API key is set (after loading .env)
source .env
echo $ANTHROPIC_API_KEY | cut -c1-20
```

---

## 🎯 Best Practices

### ✅ DO
- ✅ Use `.env` for API keys
- ✅ Keep `.env` in `.gitignore`
- ✅ Share `.env.example` (without real key)
- ✅ Use start script for convenience

### ❌ DON'T
- ❌ Commit `.env` to git
- ❌ Share `.env` publicly
- ❌ Hardcode keys in source code
- ❌ Email API keys

---

## 🚀 Production Deployment

For production servers:

### Option 1: System Environment Variables
```bash
# Add to /etc/environment
ANTHROPIC_API_KEY=your-key

# Or add to systemd service
[Service]
Environment="ANTHROPIC_API_KEY=your-key"
```

### Option 2: Docker
```yaml
# docker-compose.yml
environment:
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# .env file (not committed)
ANTHROPIC_API_KEY=your-key
```

### Option 3: Cloud Secrets
- AWS: Use AWS Secrets Manager
- GCP: Use Secret Manager
- Azure: Use Key Vault
- Heroku: Use Config Vars

---

## 📝 Summary

✅ **Your Setup is Perfect!**

- `.env` file created
- API key stored securely
- Added to `.gitignore`
- Easy start script available

**Just run**: `./start_with_env.sh`

---

*Last updated: 2025-11-29*
*Status: Secure and ready to use* ✅

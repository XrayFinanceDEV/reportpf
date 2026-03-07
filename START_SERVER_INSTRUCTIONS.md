# How to Start the API Server

**V3 API Server requires an Anthropic API Key**

---

## 🚀 Quick Start (Recommended)

### Option 1: Use the Start Script

```bash
./start_server.sh
```

This script:
- ✅ Sets the API key automatically
- ✅ Activates virtual environment
- ✅ Starts the server on port 8001

---

## 🔧 Manual Start

### Option 2: Set Environment Variable Manually

```bash
# 1. Set API key
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"

# 2. Activate virtual environment
source venv/bin/activate

# 3. Start server
python api_server.py
```

### Option 3: Use .env File

```bash
# 1. Copy example env file
cp .env.example .env

# 2. Load environment variables
source .env

# 3. Activate venv and start
source venv/bin/activate
python api_server.py
```

---

## ✅ Verify Server is Running

Once started, you should see:

```
🚀 Avvio FastAPI Server - Report Società di Persone
====================================================================
📍 Server URL: http://localhost:8001
📖 API Docs: http://localhost:8001/docs
```

Test with:
```bash
curl http://localhost:8001/
```

Expected response:
```json
{
  "message": "Report Società di Persone - PDF Extractor API",
  "version": "3.0.0",
  "extractor": "V3 - Claude Haiku 3.5 (LLM-powered, no OCR)"
}
```

---

## 🧪 Test the API

### Upload PDFs

```bash
curl -X POST http://localhost:8001/upload/process \
  -F "pdf_anno_corrente=@USP UNICO REDDITI TESSITURA 2024.pdf" \
  -F "pdf_anno_precedente=@USP UNICO REDDITI TESSITURA 2023.pdf"
```

Or use the Swagger UI at: http://localhost:8001/docs

---

## ⚠️ Troubleshooting

### Error: "Could not resolve authentication method"

**Problem**: API key not set

**Solution**: Use one of the methods above to set `ANTHROPIC_API_KEY`

### Error: "Anthropic API key not found"

**Problem**: Environment variable not exported

**Solution**:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Error: "No module named 'anthropic'"

**Problem**: Dependencies not installed

**Solution**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Server won't start - Port already in use

**Problem**: Port 8001 is busy

**Solution**:
```bash
# Kill existing process
lsof -ti:8001 | xargs kill

# Or use different port
uvicorn api_server:app --port 8002
```

---

## 📝 API Key Security

**Important**: Never commit your API key to git!

The API key is already in:
- ✅ `start_server.sh` (for convenience)
- ✅ `.env.example` (as template)

If sharing code:
1. Remove API key from `start_server.sh`
2. Don't commit `.env` file
3. Use `.env.example` as template only

---

## 🎯 Production Deployment

For production, use environment variables instead of hardcoded keys:

```bash
# Set in system environment
export ANTHROPIC_API_KEY="your-production-key"

# Start with uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 8001 --workers 4
```

Or use systemd service, Docker, etc.

---

*Last updated: 2025-11-29*
*V3 API Server - Claude Haiku 3.5*

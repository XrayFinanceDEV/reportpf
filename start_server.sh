#!/bin/bash

# start_server.sh
# Script per avviare il FastAPI server

# Get script directory and cd to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "=========================================="
echo "🚀 Avvio FastAPI Server"
echo "Report Società di Persone - PDF Extractor"
echo "=========================================="
echo ""

# Load .env file if it exists
if [ -f ".env" ]; then
    echo "📄 Caricamento variabili da .env..."
    set -a
    source .env
    set +a
    echo "✅ File .env caricato"

    # Verify API key
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "⚠️  Warning: ANTHROPIC_API_KEY non trovato in .env"
    else
        echo "✅ API Key configurata"
    fi
else
    echo "⚠️  File .env non trovato - assicurati che ANTHROPIC_API_KEY sia configurato"
fi

echo ""

# Verifica che il virtual environment esista
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment non trovato!"
    echo "Esegui prima: python3 -m venv venv"
    exit 1
fi

# Attiva il virtual environment
echo "📦 Attivazione virtual environment..."
source venv/bin/activate

# Verifica che le dipendenze siano installate
echo "🔍 Verifica dipendenze..."
if ! python -c "import fastapi, uvicorn, pdfplumber" 2>/dev/null; then
    echo "⚠️  Alcune dipendenze mancano. Installazione in corso..."
    pip install -r requirements.txt
fi

echo ""
echo "✅ Ambiente pronto!"
echo ""
echo "📍 Server URL: http://localhost:8001"
echo "📖 API Docs (Swagger): http://localhost:8001/docs"
echo "📄 API Docs (ReDoc): http://localhost:8001/redoc"
echo ""
echo "Premi CTRL+C per fermare il server"
echo ""

# Avvia il server
python api_server.py

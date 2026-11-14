#!/bin/bash
# Setup script for Gemini API key
# Run: bash setup-gemini.sh
# Or:  GEMINI_KEY=your_key_here bash setup-gemini.sh

set -e

BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$BACKEND_DIR/.env"

echo "=== Gemini API Key Setup ==="
echo "This writes your Gemini API key to $ENV_FILE (gitignored, not committed)."
echo ""

if [ -n "$GEMINI_KEY" ]; then
    KEY="$GEMINI_KEY"
    echo "Using GEMINI_KEY env var."
elif [ -n "$(command ls -la "$ENV_FILE" 2>/dev/null | grep GEMINI_API_KEY)" ]; then
    KEY=$(grep GEMINI_API_KEY "$ENV_FILE" | head -1 | cut -d= -f2)
    echo "Found existing key in .env (showing first 8 chars): ${KEY:0:8}..."
    echo ""
    read -p "Replace it? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Keeping existing key."
        exit 0
    fi
fi

if [ -z "$KEY" ]; then
    echo ""
    echo "Paste your Gemini API key (from https://aistudio.google.com/apikey):"
    read -s KEY
    echo ""
    if [ -z "$KEY" ]; then
        echo "ERROR: No key provided."
        exit 1
    fi
fi

# Write/update .env
if [ -f "$ENV_FILE" ]; then
    if grep -q "^GEMINI_API_KEY=" "$ENV_FILE" 2>/dev/null; then
        sed -i "s/^GEMINI_API_KEY=.*/GEMINI_API_KEY=$KEY/" "$ENV_FILE"
    else
        echo "GEMINI_API_KEY=$KEY" >> "$ENV_FILE"
    fi
else
    cat > "$ENV_FILE" << EOF
# Gemini API key (get from https://aistudio.google.com/apikey)
GEMINI_API_KEY=$KEY
GEMINI_MODEL=gemini-flash-latest

# Ollama (optional — leave blank if not using local Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
EOF
fi

echo ""
echo "=== Done ==="
echo "Key set in $ENV_FILE"
echo "Restart backend: cd $BACKEND_DIR && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

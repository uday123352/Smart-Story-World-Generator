#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  WorldForge AI — Setup & Run Script
#  Usage:  chmod +x run.sh && ./run.sh
# ═══════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║       ⚔  WorldForge AI  ⚔                ║"
echo "║   AI Smart Story World Generator          ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ── Load .env file if present ────────────────────────────────────────
if [ -f "$SCRIPT_DIR/.env" ]; then
  echo "📄 Loading .env file..."
  set -o allexport
  # shellcheck disable=SC1090
  source "$SCRIPT_DIR/.env"
  set +o allexport
  echo "✅ Environment variables loaded"
fi

# ── Check Python ─────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 is required. Please install it from https://python.org"
  exit 1
fi
PYTHON=$(command -v python3)
echo "✅ Python: $($PYTHON --version)"

# ── Check / create virtual environment ───────────────────────────────
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "📦 Creating virtual environment..."
  $PYTHON -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "✅ Virtual environment active"

# ── Install dependencies ──────────────────────────────────────────────
echo "📦 Installing Python dependencies..."
pip install -q -r "$SCRIPT_DIR/backend/requirements.txt"
echo "✅ Dependencies installed"

# ── Check for API key ─────────────────────────────────────────────────
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo ""
  echo "⚠️  ANTHROPIC_API_KEY is not set."
  echo "   Option 1: Create a .env file in this directory with:"
  echo "             ANTHROPIC_API_KEY=sk-ant-your-key-here"
  echo "   Option 2: export ANTHROPIC_API_KEY=your_key_here"
  echo "   Get a key at: https://console.anthropic.com"
  echo ""
  read -r -p "   Enter your Anthropic API key now (or press Enter to skip): " key
  if [ -n "$key" ]; then
    export ANTHROPIC_API_KEY="$key"
    echo "✅ API key set for this session."
  else
    echo "   ⚠️  Continuing without API key — AI generation will return errors."
  fi
fi

# ── Create database directory ─────────────────────────────────────────
mkdir -p "$SCRIPT_DIR/database"

# ── Launch server ─────────────────────────────────────────────────────
echo ""
echo "🚀 Starting WorldForge AI server..."
echo "   → http://127.0.0.1:5000"
echo ""
echo "   Press Ctrl+C to stop."
echo ""

cd "$SCRIPT_DIR/backend"
$PYTHON app.py

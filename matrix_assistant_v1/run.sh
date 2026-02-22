#!/usr/bin/env bash
set -euo pipefail

echo "🔵 Ativando ambiente virtual (se existir)..."
if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
elif [ -d "venv" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

echo "🚀 Iniciando aplicação..."
if command -v streamlit >/dev/null 2>&1; then
  streamlit run app.py
else
  python3 -m streamlit run app.py
fi

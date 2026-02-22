#!/usr/bin/env bash
set -euo pipefail

MODE="ARGente"
TS="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_DIR="backups/${TS}_${MODE}"
SNAPSHOT_DIR="${BACKUP_DIR}/snapshot"

echo "📦 Criando backup em: ${BACKUP_DIR}"
mkdir -p "${SNAPSHOT_DIR}"

echo "📁 Copiando snapshot (excluindo .git e backups antigos)..."
rsync -a \
  --exclude ".git/" \
  --exclude "backups/" \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  --exclude ".venv/" \
  --exclude "venv/" \
  "./" "${SNAPSHOT_DIR}/"

echo "📝 Salvando informações de versionamento..."
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git rev-parse HEAD > "${BACKUP_DIR}/commit_hash.txt" 2>/dev/null || true
  git status --porcelain > "${BACKUP_DIR}/git_status.txt" 2>/dev/null || true
  git diff > "${BACKUP_DIR}/diff.txt" 2>/dev/null || true
else
  echo "Projeto não é um repositório git." > "${BACKUP_DIR}/git_status.txt"
fi

cat > "${BACKUP_DIR}/metadata.json" <<META
{
  "timestamp": "${TS}",
  "mode": "${MODE}",
  "kind": "UI_Effects",
  "rollback": {
    "snapshot_dir": "snapshot",
    "instructions": "Para rollback, copie snapshot/ de volta para a raiz do projeto."
  }
}
META

echo "✅ Backup ARGente criado com sucesso!"
echo "➡️  Snapshot: ${SNAPSHOT_DIR}"

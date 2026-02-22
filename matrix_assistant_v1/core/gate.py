from __future__ import annotations
import re
from typing import List, Tuple
from .schemas import Patch, AuditReport

BANNED_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bmkfs\b",
    r"\bdd\b",
    r"\bcurl\b.*\|\s*\bbash\b",
]

CRITICAL_PATH_PREFIXES = ("/etc", "/usr", "/var", "/bin", "/sbin", "/root")

def is_absolute_path(p: str) -> bool:
    return p.startswith("/")

def analyze_patch(patch: Patch, workspace_root: str) -> AuditReport:
    reasons: List[str] = []
    blocked = False
    needs_user_review = False
    needs_sudo_review = False

    # manifest files must be relative by default
    for f in patch.manifest.files:
        if is_absolute_path(f):
            reasons.append(f"Arquivo no manifest é absoluto: {f}")
            needs_user_review = True

    # commands checks
    last_idx = 0
    for c in patch.commands:
        if c.step_index <= last_idx:
            reasons.append("step_index não é estritamente crescente")
            blocked = True
        last_idx = c.step_index

        cmd = c.cmd.strip()
        if c.privilege == "sudo" or cmd.startswith("sudo "):
            needs_sudo_review = True

        # block dangerous patterns
        for pat in BANNED_PATTERNS:
            if re.search(pat, cmd):
                blocked = True
                reasons.append(f"Comando bloqueado por padrão perigoso: {pat}")
        # critical path writes hint
        if any(cmd.find(pref) != -1 for pref in CRITICAL_PATH_PREFIXES):
            needs_user_review = True
            reasons.append("Comando toca em caminho crítico do sistema (revisão obrigatória).")

        # workspace hint: if writing outside workspace, review
        if workspace_root and is_absolute_path(workspace_root):
            # heurística: se comando contém caminho absoluto fora do workspace
            m = re.findall(r"(/[^\s]+)", cmd)
            for path in m:
                if path.startswith("/") and (not path.startswith(workspace_root)):
                    # ignore common binaries like /usr/bin/...
                    if path.startswith(CRITICAL_PATH_PREFIXES):
                        continue
                    needs_user_review = True
                    reasons.append(f"Comando referencia caminho fora do workspace: {path}")

    return AuditReport(
        needs_user_review=needs_user_review,
        needs_sudo_review=needs_sudo_review,
        blocked=blocked,
        reasons=reasons,
    )

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ============================================================
# Boot: permitir rodar pela RAIZ
# Repo root/
#   app.py  <-- este arquivo
#   matrix_assistant_v1/
#       core/
#       tools/
#       tests/
#       ...
# ============================================================

REPO_ROOT = Path(__file__).resolve().parent
APP_DIR = REPO_ROOT / "matrix_assistant_v1"

# Garante que "import core.xxx" resolva para matrix_assistant_v1/core
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Agora esses imports funcionam rodando pela raiz
from core.orchestrator import run_pipeline
from core.executor import execute_commands
from core.schemas import Patch
from core.memory import init_db, save_episode
from core.metrics import compute_sfc

load_dotenv()

st.set_page_config(page_title="Matrix Assistant", page_icon="🟢", layout="wide")

# -----------------------------
# Base visual (Matrix)
# -----------------------------
MATRIX_CSS = """
<style>
/* Matrix aesthetic */
html, body, [class*="css"]  { background: #050805 !important; color: #b6ffb6 !important; }
a { color: #38ff5a !important; }
.block-container { padding-top: 1.5rem; }
h1,h2,h3 { color: #38ff5a !important; letter-spacing: 0.02em; }
code, pre { background: rgba(0,0,0,0.65) !important; color: #b6ffb6 !important; border: 1px solid rgba(56,255,90,0.25) !important; }

.stButton>button {
  border: 1px solid rgba(56,255,90,0.55);
  background: rgba(0,0,0,0.35);
  color: #b6ffb6;
  border-radius: 12px;
}
.stButton>button:hover { border-color: #38ff5a; }

.stTextInput input, .stTextArea textarea {
  background: rgba(0,0,0,0.45) !important;
  color: #b6ffb6 !important;
  border: 1px solid rgba(56,255,90,0.35) !important;
  border-radius: 12px !important;
}

.matrix-hud {
  border: 1px solid rgba(56,255,90,0.35);
  background: rgba(0,0,0,0.45);
  border-radius: 16px;
  padding: 12px 14px;
  margin-bottom: 12px;
  box-shadow: 0 0 18px rgba(56,255,90,0.10);
}
.matrix-badge {
  display:inline-block;
  padding: 2px 10px;
  border: 1px solid rgba(56,255,90,0.35);
  border-radius: 999px;
  margin-right: 8px;
  background: rgba(0,0,0,0.35);
}
.matrix-sep { height:1px; background: rgba(56,255,90,0.18); margin: 10px 0; }

#matrix-bg {
  position: fixed; inset: 0; z-index: -1; opacity: 0.35;
}
</style>
"""

MATRIX_CANVAS = """
<canvas id="matrix-bg"></canvas>
<script>
const canvas = document.getElementById('matrix-bg');
const ctx = canvas.getContext('2d');

function resize(){
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

const letters = 'アイウエオカキクケコサシスセソタチツテトナニヌネノ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const fontSize = 14;
let columns = Math.floor(canvas.width / fontSize);
let drops = Array(columns).fill(1);

function draw(){
  ctx.fillStyle = 'rgba(5, 8, 5, 0.08)';
  ctx.fillRect(0,0,canvas.width,canvas.height);

  ctx.fillStyle = '#38ff5a';
  ctx.font = fontSize + 'px monospace';

  for(let i=0;i<drops.length;i++){
    const text = letters.charAt(Math.floor(Math.random()*letters.length));
    ctx.fillText(text, i*fontSize, drops[i]*fontSize);

    if(drops[i]*fontSize > canvas.height && Math.random() > 0.975){
      drops[i]=0;
    }
    drops[i]++;
  }
  requestAnimationFrame(draw);
}
draw();
</script>
"""

# -----------------------------
# Util: carregar assets do modo ARGente (sem quebrar se não existirem)
# -----------------------------
def _read_text_if_exists(path: Path) -> str | None:
    try:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8")
    except Exception:
        return None
    return None


def apply_argente_assets(enabled: bool) -> None:
    """
    Se enabled=True, tenta carregar:
      matrix_assistant_v1/ui_modes/argente/argente.css  (injetado via st.markdown)
      matrix_assistant_v1/ui_modes/argente/argente.html (injetado via st.components.v1.html)
    """
    if not enabled:
        return

    base = APP_DIR / "ui_modes" / "argente"
    css = _read_text_if_exists(base / "argente.css")
    html = _read_text_if_exists(base / "argente.html")

    if css:
        st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)

    if html:
        st.components.v1.html(html, height=0)


# -----------------------------
# App
# -----------------------------
st.markdown(MATRIX_CSS, unsafe_allow_html=True)
st.components.v1.html(MATRIX_CANVAS, height=0)

# Sidebar config
with st.sidebar:
    st.title("🟢 Matrix Control")

    argente_mode = st.checkbox("Ativar Modo ARGente (UI/efeitos)", value=False)

    base_url = st.text_input("LLM_BASE_URL", value=os.getenv("LLM_BASE_URL", ""))
    api_key = st.text_input("LLM_API_KEY", value=os.getenv("LLM_API_KEY", ""), type="password")
    model = st.text_input("LLM_MODEL", value=os.getenv("LLM_MODEL", ""))

    workspace_root = st.text_input(
        "WORKSPACE_ROOT",
        value=os.getenv("WORKSPACE_ROOT", os.path.expanduser("~/assistant_workspace")),
    )

    allow_sudo_exec = st.checkbox(
        "Permitir executar sudo no app (não recomendado)",
        value=os.getenv("ALLOW_SUDO_EXEC", "0") == "1",
    )

    db_path = os.path.join(workspace_root, "matrix_assistant.db")
    st.caption(f"DB: {db_path}")

apply_argente_assets(argente_mode)

st.title("Matrix Assistant — Orquestrador + Executor (V1)")
st.markdown(
    '<div class="matrix-hud">'
    '<span class="matrix-badge">Modo: semi-autônomo</span>'
    '<span class="matrix-badge">SUDO: auditoria obrigatória</span>'
    '</div>',
    unsafe_allow_html=True,
)

os.makedirs(workspace_root, exist_ok=True)
init_db(db_path)

if "history" not in st.session_state:
    st.session_state.history = []

objective = st.text_input(
    "O que você quer fazer no Ubuntu/Python?",
    placeholder="Ex.: criar um projeto python com pytest e rodar testes",
)

col1, col2 = st.columns([1, 1])
with col1:
    run_btn = st.button("Gerar plano + prévia (não executa)")
with col2:
    st.caption("Depois você aprova execução passo a passo.")

if run_btn:
    if not base_url or not api_key or not model:
        st.error("Configure LLM_BASE_URL, LLM_API_KEY e LLM_MODEL na sidebar.")
    elif not objective.strip():
        st.error("Digite um objetivo.")
    else:
        with st.spinner("Gerando PLANO + PATCH via API..."):
            result = run_pipeline(base_url, api_key, model, objective.strip(), workspace_root)
        st.session_state.last = result

if "last" in st.session_state:
    last = st.session_state.last
    st.subheader("HUD")

    m = last["metrics"]
    audit = last["audit"]

    st.markdown(
        '<div class="matrix-hud">'
        f'<span class="matrix-badge">Model: {last.get("model_used","?")}</span>'
        f'<span class="matrix-badge">C={m["T"]} tarefas</span>'
        f'<span class="matrix-badge">C-score={m["C"]:.2f}</span>'
        f'<span class="matrix-badge">U={m["U"]:.2f}</span>'
        f'<span class="matrix-badge">R={m["R"]}</span>'
        f'<span class="matrix-badge">Blocked={audit["blocked"]}</span>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("### PLANO (JSON)")
    st.code(json.dumps(last["plan"], ensure_ascii=False, indent=2), language="json")

    st.markdown("### PATCH (JSON)")
    st.code(json.dumps(last["patch"], ensure_ascii=False, indent=2), language="json")

    st.markdown("### Análise de Segurança (Gate)")
    st.code(json.dumps(audit, ensure_ascii=False, indent=2), language="json")

    if audit["blocked"]:
        st.error("Execução bloqueada pelo gate. Ajuste o objetivo/prompt e gere novamente.")
    else:
        patch_obj = Patch.model_validate(last["patch"])

        cmds_user = [
            c
            for c in patch_obj.commands
            if c.privilege == "user" and not c.cmd.strip().startswith("sudo")
        ]
        cmds_sudo = [
            c
            for c in patch_obj.commands
            if c.privilege == "sudo" or c.cmd.strip().startswith("sudo")
        ]

        st.markdown("### Prévia de Execução (NÃO executado ainda)")

        st.write("**Comandos (user)**")
        for c in cmds_user:
            st.markdown(
                f"- **[{c.step_index}]** `{c.cmd}`\n"
                f"  WHY: {c.why}\n"
                f"  EXPECTS: `{c.expects_cmd}`"
            )

        if cmds_sudo:
            st.warning("**Comandos com SUDO detectados — auditoria obrigatória**")
            for c in cmds_sudo:
                st.markdown(
                    f"- **[S{c.step_index}]** `{c.cmd}`\n"
                    f"  WHY: {c.why}\n"
                    f"  EXPECTS: `{c.expects_cmd}`"
                )

        st.markdown('<div class="matrix-sep"></div>', unsafe_allow_html=True)

        st.subheader("Autorizar execução")
        approve_user = st.checkbox("Aprovar comandos SEM sudo", value=True)
        approve_sudo = st.checkbox("Aprovar comandos COM sudo (exige auditoria e confirmação)", value=False)

        confirm = st.text_input("Confirmação (digite exatamente): EXECUTAR", value="")
        sudo_phrase = st.text_input("Se aprovar sudo, digite exatamente: AUTORIZO_SUDO", value="")

        if st.button("Executar agora"):
            if confirm.strip() != "EXECUTAR":
                st.error("Confirmação inválida. Digite EXECUTAR.")
            elif not approve_user and not approve_sudo:
                st.error("Nenhuma execução aprovada.")
            else:
                to_run = []
                if approve_user:
                    to_run.extend(cmds_user)
                if approve_sudo:
                    if sudo_phrase.strip() != "AUTORIZO_SUDO":
                        st.error("SUDO não autorizado. Digite AUTORIZO_SUDO.")
                        st.stop()
                    to_run.extend(cmds_sudo)

                with st.spinner("Executando..."):
                    results = execute_commands(
                        to_run,
                        cwd=str(REPO_ROOT),
                        allow_sudo_exec=allow_sudo_exec,
                    )

                st.subheader("Resultados")
                st.code(
                    json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2),
                    language="json",
                )

                success = bool(results) and all((r.rc == 0 and r.expects_rc == 0) for r in results)
                had_sudo = bool(cmds_sudo)

                SS_local = 100.0 if success else 50.0
                IEC = 50.0
                IRO_total = 5.0 if success else 50.0
                sfc = compute_sfc(SS_local, IEC, IRO_total)

                st.markdown(
                    '<div class="matrix-hud">'
                    f'<span class="matrix-badge">SUCCESS={success}</span>'
                    f'<span class="matrix-badge">SFC={sfc:.2f}</span>'
                    "</div>",
                    unsafe_allow_html=True,
                )

                episode_id = save_episode(
                    db_path,
                    {
                        "user_input": objective.strip(),
                        "plan": last["plan"],
                        "patch": last["patch"],
                        "audit": audit,
                        "exec": [r.__dict__ for r in results],
                        "model_used": last.get("model_used"),
                        "approved": True,
                        "had_sudo": had_sudo,
                        "success": success,
                    },
                )
                st.success(f"Episódio salvo no DB. id={episode_id}")

st.caption("Dica: se você estiver na raiz, rode: streamlit run app.py")

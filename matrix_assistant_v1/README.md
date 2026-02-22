# Matrix Assistant V1 (uso pessoal) — Orquestrador + Executor com Auditoria

Este app é um **assistente local** (UI web) com estética **Matrix**, que:
- Usa **1 LLM via sua API** (OpenAI-compatible) para gerar **PLANO** e **PATCH** em JSON.
- Aplica **gates determinísticos** (segurança/risco) antes de executar.
- Executa comandos **após aprovação** do usuário.
- Para `sudo`, faz **auditoria obrigatória** e pode:
  - (recomendado) **gerar o comando para você executar no terminal**, ou
  - (opcional) executar `sudo` no app se você habilitar explicitamente (veja abaixo).

## 1) Instalação (Ubuntu)

```bash
mkdir -p ~/assistant_workspace
mkdir -p ~/apps && cd ~/apps
unzip matrix_assistant_v1.zip -d matrix_assistant_v1
cd matrix_assistant_v1

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 2) Configurar API (obrigatório)

Crie `.env` a partir do exemplo:

```bash
cp .env.example .env
nano .env
```

Campos:
- `LLM_BASE_URL` (ex.: https://api.seu-provedor.com/v1)
- `LLM_API_KEY`
- `LLM_MODEL` (nome do modelo)

## 3) Rodar

```bash
source .venv/bin/activate
streamlit run app.py
```

Abra o link que o Streamlit mostrar (normalmente `http://localhost:8501`).

## 4) Teste de gaveta (unit tests)

```bash
source .venv/bin/activate
pip install -U pytest
pytest -q
```

## 5) Como usar (fluxo)
1. Digite o **objetivo** (ex.: "instalar git e verificar versão").
2. O app gera:
   - **PLANO** (Planner)
   - **Métricas** (C/U/R)
   - **PATCH** (Coder): comandos + expects_cmd
3. O app mostra a **prévia**:
   - comandos sem sudo (executáveis)
   - comandos com sudo (auditoria + aprovação)
4. Você aprova e executa.
5. O app verifica, registra logs e salva no SQLite.

## 6) SUDO (modo seguro)
Por padrão o app **NÃO executa sudo automaticamente** (para evitar travar pedindo senha).
Ele gera a auditoria e mostra o comando para você executar no terminal.

Se você quiser permitir execução de `sudo` no app (não recomendado), ative no `.env`:
- `ALLOW_SUDO_EXEC=1`

E use um mecanismo de sudo não-interativo (por exemplo, NOPASSWD em sudoers para comandos específicos).
O app **não guarda senha**.

## 7) Pasta de trabalho
O app assume `WORKSPACE_ROOT` (default: `~/assistant_workspace`) e tenta manter tudo dentro dela.

---

**Nota:** Este projeto é para **uso pessoal com supervisão**. Ele não executa ações que possam prejudicar terceiros.

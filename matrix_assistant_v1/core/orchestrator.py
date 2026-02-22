from __future__ import annotations
import os, json, re
from typing import Any, Dict, Tuple, Optional, List

from .api_client import chat
from .schemas import Plan, Patch
from .metrics import compute_complexity, compute_uncertainty, compute_sfc, compute_lmax, compute_delta
from .gate import analyze_patch
from .prompts import PLANNER_PROMPT, CODER_PROMPT

def _extract_json(text: str) -> str:
    # tenta pegar o primeiro objeto JSON do texto
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError("Nenhum JSON encontrado na resposta.")
    return m.group(0)

def llm_plan(base_url: str, api_key: str, model: str, objective: str) -> Tuple[Plan, str]:
    # Schema para forçar JSON
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "Plan",
            "schema": {
                "type": "object",
                "properties": {
                    "tasks": {"type":"array","minItems":1,"items":{
                        "type":"object",
                        "properties":{
                            "task_id":{"type":"string"},
                            "objective":{"type":"string"},
                            "actions":{"type":"array","minItems":1,"items":{"type":"string"}},
                            "success_criteria":{"type":"string"}
                        },
                        "required":["task_id","objective","actions","success_criteria"]
                    }},
                    "constraints": {"type":"array","items":{"type":"string"}},
                    "artifacts": {"type":"array","items":{"type":"string"}}
                },
                "required":["tasks","constraints","artifacts"]
            }
        }
    }
    messages = [
        {"role":"system","content":PLANNER_PROMPT},
        {"role":"user","content":f"Objetivo do usuário: {objective}\nResponda SOMENTE no schema."}
    ]
    data = chat(base_url, api_key, model, messages, response_format=schema)
    model_used = data.get("model") or model
    content = data["choices"][0]["message"]["content"]
    plan = Plan.model_validate_json(_extract_json(content))
    return plan, model_used

def llm_patch(base_url: str, api_key: str, model: str, objective: str, plan: Plan) -> Tuple[Patch, str]:
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "Patch",
            "schema": {
                "type": "object",
                "properties": {
                    "manifest": {"type":"object","properties":{
                        "files":{"type":"array","minItems":1,"items":{"type":"string"}}
                    },"required":["files"]},
                    "tasks_covered": {"type":"array","minItems":1,"items":{"type":"string"}},
                    "constraints_violated": {"type":"boolean"},
                    "commands": {"type":"array","minItems":1,"items":{
                        "type":"object",
                        "properties":{
                            "step_index":{"type":"integer","minimum":1},
                            "cmd":{"type":"string"},
                            "why":{"type":"string"},
                            "expects_cmd":{"type":"string"},
                            "privilege":{"type":"string","enum":["user","sudo"]}
                        },
                        "required":["step_index","cmd","why","expects_cmd","privilege"]
                    }}
                },
                "required":["manifest","tasks_covered","constraints_violated","commands"]
            }
        }
    }
    task_ids = [t.task_id for t in plan.tasks]
    messages = [
        {"role":"system","content":CODER_PROMPT},
        {"role":"user","content":(
            f"Objetivo: {objective}\n"
            f"task_ids: {task_ids}\n"
            "Regras: usar caminhos relativos, e expects_cmd deve ser um comando verificável.\n"
            "Responda SOMENTE no schema."
        )}
    ]
    data = chat(base_url, api_key, model, messages, response_format=schema)
    model_used = data.get("model") or model
    content = data["choices"][0]["message"]["content"]
    patch = Patch.model_validate_json(_extract_json(content))
    return patch, model_used

def estimate_C_U_R(plan: Plan) -> Tuple[float,float,str,Dict[str,int]]:
    T = len(plan.tasks)
    # heurísticas simples (podem evoluir depois)
    D = sum(1 for t in plan.tasks if any("dep" in a.lower() for a in t.actions))
    K = len(plan.constraints)
    A = len(plan.artifacts)
    C = compute_complexity(T,D,K,A)

    ambiguous = 0
    total_steps = sum(len(t.actions) for t in plan.tasks)
    vague_tokens = ("talvez","aprox","aproximadamente","pode","se necessário","não aplicável","not applicable")
    for t in plan.tasks:
        txt = " ".join(t.actions+[t.success_criteria]).lower()
        if any(v in txt for v in vague_tokens):
            ambiguous += 1
    U = compute_uncertainty(ambiguous, max(1,total_steps))

    # risco determinístico (muito simples): constraints + palavras-chave
    risk = "Baixo"
    alltxt = (json.dumps(plan.model_dump(), ensure_ascii=False)).lower()
    if any(x in alltxt for x in ["sudo","/etc","firewall","porta","systemctl","kernel","driver"]):
        risk = "Alto"
    elif C >= 7 or U > 0.6:
        risk = "Médio"
    return C,U,risk,{"T":T,"D":D,"K":K,"A":A,"ambiguous":ambiguous,"total_steps":total_steps}

def run_pipeline(base_url: str, api_key: str, model: str, objective: str, workspace_root: str) -> Dict[str, Any]:
    plan, model_plan = llm_plan(base_url, api_key, model, objective)
    C,U,R,counts = estimate_C_U_R(plan)
    patch, model_patch = llm_patch(base_url, api_key, model, objective, plan)
    audit = analyze_patch(patch, workspace_root=workspace_root)
    return {
        "plan": plan.model_dump(),
        "patch": patch.model_dump(),
        "audit": audit.model_dump(),
        "metrics": {"C":C,"U":U,"R":R, **counts},
        "model_used": model_patch or model_plan or model
    }

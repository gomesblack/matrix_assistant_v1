from __future__ import annotations
import requests
from typing import Any, Dict, Optional

def chat(base_url: str, api_key: str, model: str, messages, response_format: Optional[dict]=None, timeout_s: int=120) -> Dict[str, Any]:
    # OpenAI-compatible: POST {base_url}/chat/completions
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    if response_format:
        # OpenAI JSON schema style
        payload["response_format"] = response_format
    r = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
    r.raise_for_status()
    return r.json()

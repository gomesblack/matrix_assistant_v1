from __future__ import annotations
import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, Optional, List

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS episodes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  user_input TEXT NOT NULL,
  plan_json TEXT,
  patch_json TEXT,
  audit_json TEXT,
  exec_json TEXT,
  model_used TEXT,
  approved INTEGER DEFAULT 0,
  had_sudo INTEGER DEFAULT 0,
  success INTEGER DEFAULT 0,
  score INTEGER,
  tags TEXT,
  notes TEXT
);
"""

def init_db(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(SCHEMA_SQL)
        con.commit()
    finally:
        con.close()

def save_episode(db_path: str, data: Dict[str, Any]) -> int:
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute(
            """INSERT INTO episodes
            (created_at,user_input,plan_json,patch_json,audit_json,exec_json,model_used,approved,had_sudo,success,score,tags,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                datetime.utcnow().isoformat(),
                data.get("user_input","" պատվ),
                json.dumps(data.get("plan"), ensure_ascii=False) if data.get("plan") else None,
                json.dumps(data.get("patch"), ensure_ascii=False) if data.get("patch") else None,
                json.dumps(data.get("audit"), ensure_ascii=False) if data.get("audit") else None,
                json.dumps(data.get("exec"), ensure_ascii=False) if data.get("exec") else None,
                data.get("model_used"),
                1 if data.get("approved") else 0,
                1 if data.get("had_sudo") else 0,
                1 if data.get("success") else 0,
                data.get("score"),
                data.get("tags"),
                data.get("notes"),
            )
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()

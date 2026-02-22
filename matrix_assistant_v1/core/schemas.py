from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

class Task(BaseModel):
    task_id: str
    objective: str
    actions: List[str]
    success_criteria: str

class Plan(BaseModel):
    tasks: List[Task] = Field(min_length=1)
    constraints: List[str] = []
    artifacts: List[str] = []

class Command(BaseModel):
    step_index: int = Field(ge=1)
    cmd: str
    why: str
    expects_cmd: str  # SEMPRE um comando verificável (não texto)

    privilege: Literal["user","sudo"] = "user"

    @field_validator("expects_cmd")
    @classmethod
    def expects_must_look_like_command(cls, v: str):
        # Regra simples: deve conter pelo menos um token típico de shell
        if not v or len(v.strip()) < 3:
            raise ValueError("expects_cmd vazio")
        return v.strip()

class Manifest(BaseModel):
    files: List[str] = Field(min_length=1)

class Patch(BaseModel):
    manifest: Manifest
    tasks_covered: List[str] = Field(min_length=1)
    constraints_violated: bool = False
    commands: List[Command] = Field(min_length=1)

class AuditReport(BaseModel):
    needs_user_review: bool
    needs_sudo_review: bool
    blocked: bool
    reasons: List[str] = []

from __future__ import annotations
import subprocess
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class CmdResult:
    step_index: int
    cmd: str
    rc: int
    stdout: str
    stderr: str
    expects_cmd: str
    expects_rc: int
    expects_stdout: str
    expects_stderr: str

def run_shell(cmd: str, cwd: str, timeout_s: int = 60) -> Tuple[int,str,str]:
    p = subprocess.run(
        ["bash", "-lc", cmd],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_s
    )
    return p.returncode, p.stdout, p.stderr

def execute_commands(commands, cwd: str, allow_sudo_exec: bool = False) -> List[CmdResult]:
    results: List[CmdResult] = []
    for c in commands:
        cmd = c.cmd
        if cmd.strip().startswith("sudo") and not allow_sudo_exec:
            # Não executar sudo por padrão
            results.append(CmdResult(
                step_index=c.step_index,
                cmd=cmd,
                rc=126,
                stdout="",
                stderr="SUDO não executado pelo app (modo seguro). Execute manualmente no terminal após auditoria.",
                expects_cmd=c.expects_cmd,
                expects_rc=126,
                expects_stdout="",
                expects_stderr="SUDO expects não executado pelo app.",
            ))
            break

        rc, out, err = run_shell(cmd, cwd=cwd)
        erc, eout, eerr = run_shell(c.expects_cmd, cwd=cwd)
        results.append(CmdResult(
            step_index=c.step_index,
            cmd=cmd,
            rc=rc,
            stdout=out,
            stderr=err,
            expects_cmd=c.expects_cmd,
            expects_rc=erc,
            expects_stdout=eout,
            expects_stderr=eerr
        ))
        if rc != 0 or erc != 0:
            break
    return results

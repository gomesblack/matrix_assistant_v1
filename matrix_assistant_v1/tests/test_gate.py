from core.schemas import Patch
from core.gate import analyze_patch

def test_block_rm_rf():
    patch = Patch.model_validate({
        "manifest":{"files":["x.txt"]},
        "tasks_covered":["t1"],
        "constraints_violated": False,
        "commands":[{"step_index":1,"cmd":"rm -rf /","why":"bad","expects_cmd":"true","privilege":"user"}]
    })
    audit = analyze_patch(patch, workspace_root="/home/x/work")
    assert audit.blocked is True
    assert any("padrão perigoso" in r for r in audit.reasons)

def test_detect_sudo():
    patch = Patch.model_validate({
        "manifest":{"files":["x.txt"]},
        "tasks_covered":["t1"],
        "constraints_violated": False,
        "commands":[{"step_index":1,"cmd":"sudo apt update","why":"need","expects_cmd":"true","privilege":"sudo"}]
    })
    audit = analyze_patch(patch, workspace_root="/home/x/work")
    assert audit.needs_sudo_review is True

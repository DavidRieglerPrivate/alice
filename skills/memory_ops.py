from core.memory import wipe
from skills._base import SkillResult


def handle_wipe_memory() -> SkillResult:
    wipe()
    return SkillResult(response="Memory wiped. I have forgotten all previous conversations.", success=True)

import re

from skills._base import SkillResult
from skills.launch_app import handle_close, handle_launch

_OPEN_RE  = re.compile(r'^(?:open|launch|start|run)\s+(.+)', re.IGNORECASE)
_CLOSE_RE = re.compile(r'^(?:close|quit|exit|kill|stop|shut\s+down)\s+(.+)', re.IGNORECASE)


def route(command: str) -> SkillResult | None:
    """Return a SkillResult if a skill handled the command, or None to fall through to the LLM."""
    cmd = command.strip()
    if m := _OPEN_RE.match(cmd):
        return handle_launch(m.group(1))
    if m := _CLOSE_RE.match(cmd):
        return handle_close(m.group(1))
    return None

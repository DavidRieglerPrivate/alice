import re

from skills._base import SkillResult
from skills.file_ops import handle_open_file, handle_search_file
from skills.launch_app import handle_close, handle_launch

_FILE_EXTS = (
    r'txt|py|ts|js|jsx|tsx|json|md|pdf|doc|docx|xls|xlsx|csv|html|htm|css|xml'
    r'|yaml|yml|ini|cfg|log|bat|sh|ps1|cpp|c|h|java|rb|go|rs|swift|kt|vue'
    r'|svelte|toml|sql|db|png|jpg|jpeg|gif|bmp|svg|mp4|mp3|wav|zip|rar|7z'
)

# "search for a file called X" / "find file named X" / "look for test.txt"
_SEARCH_FILE_RE = re.compile(
    r'^(?:search(?:\s+for)?|find|look\s+for|locate|where(?:\s+is)?)\s+'
    r'(?:'
    r'(?:a\s+|the\s+)?file\s+(?:called|named)?\s*(.+)'      # with "file" keyword
    r'|(?:a\s+|the\s+)?(\S+\.(?:' + _FILE_EXTS + r'))\b'   # bare filename.ext
    r')',
    re.IGNORECASE,
)

# "open the file called X"  OR  "open test.txt" / "open test.py"
_OPEN_FILE_RE = re.compile(
    r'^(?:open|show)\s+(?:(?:a|the)\s+)?file\s+(?:called|named)?\s*(.+)'
    r'|^(?:open|show)\s+(?:(?:a|the)\s+)?(\S+\.(?:' + _FILE_EXTS + r'))\b',
    re.IGNORECASE,
)

_OPEN_RE  = re.compile(r'^(?:open|launch|start|run)\s+(.+)', re.IGNORECASE)
_CLOSE_RE = re.compile(r'^(?:close|quit|exit|kill|stop|shut\s+down)\s+(.+)', re.IGNORECASE)


def route(command: str) -> SkillResult | None:
    """Return a SkillResult if a skill handled the command, or None to fall through to the LLM."""
    cmd = command.strip()

    if m := _SEARCH_FILE_RE.match(cmd):
        return handle_search_file(m.group(1) or m.group(2))
    if m := _OPEN_FILE_RE.match(cmd):
        return handle_open_file(m.group(1) or m.group(2))
    if m := _OPEN_RE.match(cmd):
        return handle_launch(m.group(1))
    if m := _CLOSE_RE.match(cmd):
        return handle_close(m.group(1))
    return None

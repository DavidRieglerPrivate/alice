import re

from skills._base import SkillResult
from skills.calculator import handle_calculate
from skills.file_ops import handle_open_file, handle_search_file
from skills.launch_app import handle_close, handle_launch
from skills.memory_ops import handle_wipe_memory
from skills.weather import (
    handle_current_weather,
    handle_day_after_tomorrow,
    handle_tomorrow_weather,
    handle_umbrella,
    handle_weather_forecast,
    handle_week_outlook,
)

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

_OPEN_RE  = re.compile(r'^(?:open|launch|start|run)\s+(?:the\s+|a\s+|an\s+)?(.+)', re.IGNORECASE)
_CLOSE_RE = re.compile(r'^(?:close|quit|exit|kill|stop|shut\s+down)\s+(?:the\s+|a\s+|an\s+)?(.+)', re.IGNORECASE)

_WIPE_MEMORY_RE = re.compile(
    r'^(?:wipe|clear|reset|forget|erase|delete)\s+(?:your\s+)?(?:memory|conversation|history|chat)',
    re.IGNORECASE,
)

# "calculate 5 + 3" / "compute 10 times 4" / "work out 2 to the power of 8"
_CALC_CMD_RE = re.compile(
    r'^(?:calculate|calc|compute|solve|evaluate|eval|work\s+out|figure\s+out|determine)\s+(.+)',
    re.IGNORECASE,
)

# "what is 5 + 3?" / "what's 10 times 4" / "how much is 100 divided by 4"
# Only routes when the expression starts with a number or sqrt — avoids hijacking
# general "what is X" questions that don't look like math.
_CALC_QUERY_RE = re.compile(
    r'^(?:'
    r"what(?:'s|\s+is|\s+would\s+be)\s+(?:the\s+)?(?:result\s+of\s+|answer\s+(?:to|for)\s+|value\s+of\s+)?"
    r'|how\s+(?:much|many)\s+(?:is|are)\s+'
    r'|what\s+does\s+'
    r')'
    r'((?:-?\d|sqrt(?:\s+of)?\s|square\s+root\s+of\s).+?)(?:\s*\?)?$',
    re.IGNORECASE,
)

# "should I bring an umbrella [today/tomorrow/this week] [in X]?"
_WEATHER_UMBRELLA_RE = re.compile(
    r'^(?:should\s+i|do\s+i\s+need\s+(?:to\s+)?|will\s+i\s+need\s+(?:to\s+)?)'
    r'\s*(?:bring\s+|take\s+|pack\s+)?'
    r'(?:an?\s+)?(?:umbrella|rain\s+jacket|raincoat)'
    r'(?:\s+(today|tomorrow|this\s+week))?'
    r'(?:\s+(?:in|at|for)\s+(.+?))?\s*\??\s*$',
    re.IGNORECASE,
)

# "weather this week" / "weekly forecast" / "will it rain this week"
_WEATHER_WEEK_RE = re.compile(
    r'^(?:'
    r"(?:is\s+it|will\s+it)\s+(?:gonna\s+|going\s+to\s+)?rain\s+this\s+week"
    r"|what(?:'s|\s+is)\s+(?:the\s+)?weather(?:\s+like)?\s+this\s+week"
    r"|weather\s+(?:this\s+week|for\s+(?:the\s+)?week)"
    r"|weekly\s+forecast"
    r"|what(?:'s|\s+is)\s+(?:the\s+)?forecast\s+(?:for\s+)?this\s+week"
    r")(?:\s+(?:in|at|for)\s+(.+?))?\s*\??\s*$",
    re.IGNORECASE,
)

# "weather the day after tomorrow" / "will it rain the day after tomorrow"
_WEATHER_DAY_AFTER_RE = re.compile(
    r'^(?:'
    r"what(?:'s|\s+is)\s+(?:the\s+)?weather(?:\s+like)?(?:\s+(?:gonna\s+be|going\s+to\s+be|be))?\s+(?:(?:for|on|the)\s+)?day\s+after\s+tomorrow"
    r"|what\s+will\s+(?:the\s+)?weather\s+be\s+(?:the\s+)?day\s+after\s+tomorrow"
    r"|will\s+it\s+rain\s+(?:the\s+)?day\s+after\s+tomorrow"
    r"|weather\s+(?:(?:for|on|the)\s+)?(?:the\s+)?day\s+after\s+tomorrow"
    r"|(?:the\s+)?day\s+after\s+tomorrow(?:'s)?\s+(?:weather|forecast)"
    r")(?:\s+(?:in|at|for)\s+(.+?))?\s*\??\s*$",
    re.IGNORECASE,
)

# "what's the weather tomorrow" / "weather tomorrow" / "will it rain tomorrow"
_WEATHER_TOMORROW_RE = re.compile(
    r'^(?:'
    r"what(?:'s|\s+is)\s+(?:the\s+)?weather(?:\s+like)?(?:\s+(?:gonna\s+be|going\s+to\s+be|be))?\s+tomorrow"
    r"|what\s+will\s+(?:the\s+)?weather\s+be\s+tomorrow"
    r"|how(?:'s|\s+is)\s+(?:the\s+)?weather\s+tomorrow"
    r"|how\s+will\s+it\s+be\s+tomorrow"
    r"|tomorrow(?:'s)?\s+(?:weather|forecast)"
    r"|weather\s+(?:(?:for|on)\s+)?tomorrow"
    r"|will\s+it\s+rain\s+tomorrow"
    r")(?:\s+(?:in|at|for)\s+(.+?))?\s*\??\s*$",
    re.IGNORECASE,
)

# "weather forecast [for X]" / "will it rain today [in X]" / "what's the forecast [for X]"
_WEATHER_FORECAST_RE = re.compile(
    r'^(?:'
    r"what(?:'s|\s+is)\s+(?:the\s+)?forecast(?:\s+(?:for|in|at)\s+(.+?))?"
    r"|weather\s+forecast(?:\s+(?:for|in|at)\s+(.+?))?"
    r"|forecast(?:\s+(?:for|in|at)\s+(.+?))?"
    r"|will\s+it\s+rain(?:\s+today)?(?:\s+(?:in|at|for)\s+(.+?))?"
    r')\s*\??\s*$',
    re.IGNORECASE,
)

# "what's the weather [in X]" / "how hot is it" / "temperature in X" / "weather [in X]"
_WEATHER_NOW_RE = re.compile(
    r'^(?:'
    r"what(?:'s|\s+is)\s+(?:the\s+)?weather(?:\s+like)?(?:\s+(?:in|at|for)\s+(.+?))?"
    r"|what(?:'s|\s+is)\s+it\s+like\s+(?:outside|out|today)(?:\s+(?:in|at|for)\s+(.+?))?"
    r"|how(?:'s|\s+is)\s+(?:the\s+)?weather(?:\s+like)?(?:\s+(?:in|at|for)\s+(.+?))?"
    r"|how\s+(?:hot|cold|warm)\s+is\s+it(?:\s+(?:in|at|for)\s+(.+?))?"
    r"|current\s+weather(?:\s+(?:in|at|for)\s+(.+?))?"
    r"|(?:what(?:'s|\s+is)\s+(?:the\s+)?)?temperature(?:\s+(?:in|at|for)\s+(.+?))?"
    r"|weather(?:\s+(?:in|at|for)\s+(.+?))?"
    r')\s*\??\s*$',
    re.IGNORECASE,
)

# Bare math expressions: "5 + 3", "5 plus 3 times 2", "sqrt of 9", "5 squared"
_CALC_BARE_RE = re.compile(
    r'^(?:'
    r'-?\d+(?:\.\d+)?\s*(?:[+\-*/^%]|\*\*)\s*-?\d'
    r'|-?\d+(?:\.\d+)?\s+(?:plus|minus|times|multiplied\s+by|divided\s+by|over|mod(?:ulo)?'
        r'|to\s+the|raised\s+to|squ?ared?|cubed?)'
    r'|(?:square\s+root\s+of|sqrt(?:\s+of)?)\s+-?\d'
    r')',
    re.IGNORECASE,
)


def route(command: str) -> SkillResult | None:
    """Return a SkillResult if a skill handled the command, or None to fall through to the LLM."""
    cmd = command.strip()

    if _WIPE_MEMORY_RE.match(cmd):
        return handle_wipe_memory()
    if m := _WEATHER_UMBRELLA_RE.match(cmd):
        return handle_umbrella(m.group(2) or "", (m.group(1) or "today").lower().strip())
    if m := _WEATHER_WEEK_RE.match(cmd):
        return handle_week_outlook(next((g for g in m.groups() if g), ""))
    if m := _WEATHER_DAY_AFTER_RE.match(cmd):
        return handle_day_after_tomorrow(next((g for g in m.groups() if g), ""))
    if m := _WEATHER_TOMORROW_RE.match(cmd):
        return handle_tomorrow_weather(next((g for g in m.groups() if g), ""))
    if m := _WEATHER_FORECAST_RE.match(cmd):
        return handle_weather_forecast(next((g for g in m.groups() if g), ""))
    if m := _WEATHER_NOW_RE.match(cmd):
        return handle_current_weather(next((g for g in m.groups() if g), ""))
    if m := _SEARCH_FILE_RE.match(cmd):
        return handle_search_file(m.group(1) or m.group(2))
    if m := _OPEN_FILE_RE.match(cmd):
        return handle_open_file(m.group(1) or m.group(2))
    if m := _OPEN_RE.match(cmd):
        return handle_launch(m.group(1))
    if m := _CLOSE_RE.match(cmd):
        return handle_close(m.group(1))
    if m := _CALC_CMD_RE.match(cmd):
        return handle_calculate(m.group(1))
    if m := _CALC_QUERY_RE.match(cmd):
        return handle_calculate(m.group(1))
    if _CALC_BARE_RE.match(cmd):
        return handle_calculate(cmd)
    return None

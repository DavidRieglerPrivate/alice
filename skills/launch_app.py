import glob
import os
import random
import subprocess

from skills._base import SkillResult

# Well-known app name -> executable name (resolved via PATH or shell=True)
KNOWN_APPS: dict[str, str] = {
    "file explorer":          "explorer.exe",
    "explorer":               "explorer.exe",
    "notepad":                "notepad.exe",
    "calculator":             "calc.exe",
    "paint":                  "mspaint.exe",
    "task manager":           "taskmgr.exe",
    "control panel":          "control.exe",
    "cmd":                    "cmd.exe",
    "command prompt":         "cmd.exe",
    "powershell":             "powershell.exe",
    "terminal":               "wt.exe",
    "windows terminal":       "wt.exe",
    "edge":                   "msedge.exe",
    "microsoft edge":         "msedge.exe",
    "chrome":                 "chrome.exe",
    "google chrome":          "chrome.exe",
    "firefox":                "firefox.exe",
    "spotify":                "Spotify.exe",
    "discord":                "Discord.exe",
    "steam":                  "steam.exe",
    "epic games":             "EpicGamesLauncher.exe",
    "epic games launcher":    "EpicGamesLauncher.exe",
    "epic launcher":          "EpicGamesLauncher.exe",
    "vs code":                "Code.exe",
    "visual studio code":     "Code.exe",
    "vscode":                 "Code.exe",
    "word":                   "WINWORD.EXE",
    "excel":                  "EXCEL.EXE",
    "powerpoint":             "POWERPNT.EXE",
    "outlook":                "OUTLOOK.EXE",
    "teams":                  "ms-teams.exe",
    "slack":                  "slack.exe",
    "zoom":                   "Zoom.exe",
    "obs":                    "obs64.exe",
    "vlc":                    "vlc.exe",
    "zen":                    "zen.exe",
    "zen browser":            "zen.exe",
}

# App name → process image name used by taskkill (when different from KNOWN_APPS)
_CLOSE_PROC: dict[str, str] = {
    "file explorer": "explorer.exe",
    "explorer":      "explorer.exe",
}

_OPEN_REPLIES  = ["Right away, sir.", "On it.", "Opening that now.", "Sure thing."]
_CLOSE_REPLIES = ["Done.", "Closed.", "Consider it done.", "All done."]
_FAIL_OPEN     = "I couldn't find that application, sir."
_FAIL_CLOSE    = "I couldn't close that — it may not be running."


def _find_in_start_menu(app_name: str) -> str | None:
    """Return the path to the best-matching .lnk in the Start Menu, or None."""
    dirs = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    ]
    needle = app_name.lower()
    for d in dirs:
        for lnk in glob.glob(os.path.join(d, "**", "*.lnk"), recursive=True):
            name = os.path.splitext(os.path.basename(lnk))[0].lower()
            if needle in name or name in needle:
                return lnk
    return None


def handle_launch(app_name: str) -> SkillResult:
    key = app_name.lower().strip(" .,")
    exe = KNOWN_APPS.get(key)
    try:
        # Start Menu covers user-installed apps.
        lnk = _find_in_start_menu(key)
        if lnk:
            os.startfile(lnk)
        elif exe:
            # System apps (notepad, calculator, explorer…) live in PATH — run directly.
            subprocess.Popen([exe], shell=True)
        else:
            return SkillResult(response=_FAIL_OPEN, success=False)
        return SkillResult(response=random.choice(_OPEN_REPLIES), success=True)
    except Exception:
        return SkillResult(response=_FAIL_OPEN, success=False)


def handle_close(app_name: str) -> SkillResult:
    key = app_name.lower().strip(" .,")
    proc = _CLOSE_PROC.get(key) or KNOWN_APPS.get(key)

    candidates: list[str]
    if proc:
        candidates = [proc]
    else:
        # Try first-word.exe first (e.g. "zen browser" → "zen.exe"),
        # then the joined form (e.g. "zenbrowser.exe") as a last resort.
        first_word = key.split()[0]
        candidates = [first_word + ".exe", key.replace(" ", "") + ".exe"]

    try:
        for candidate in candidates:
            result = subprocess.run(
                ["taskkill", "/IM", candidate, "/F"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                return SkillResult(response=random.choice(_CLOSE_REPLIES), success=True)
        return SkillResult(response=_FAIL_CLOSE, success=False)
    except Exception:
        return SkillResult(response=_FAIL_CLOSE, success=False)

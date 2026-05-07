import os
import random
import subprocess
from pathlib import Path

from skills._base import SkillResult

_SEARCH_REPLIES = [
    "Of course, sir. Opening the folder now.",
    "Found it. Opening the directory for you, sir.",
    "Right away, sir.",
]
_OPEN_REPLIES = [
    "Of course, sir. Opening it now.",
    "Found it. Opening the file for you, sir.",
    "Right away, sir.",
]
_NOT_FOUND = "I'm afraid I couldn't find a file with that name, sir."
_OPEN_FAIL = "I found the file but couldn't open it, sir."


def _search_roots() -> list[str]:
    home = Path.home()
    candidates = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Pictures",
        home / "Videos",
        home / "Music",
    ]
    if home.exists():
        for p in home.iterdir():
            if p.is_dir() and p.name.lower().startswith("onedrive"):
                candidates.append(p)
    return [str(p) for p in candidates if p.exists()]


_SKIP_DIRS = {"AppData", "node_modules", "__pycache__", ".git", "venv", ".venv"}


def _find_files(name: str, max_results: int = 5) -> list[Path]:
    name = name.strip(" .,'\"`")
    name_lower = name.lower()
    has_ext = "." in name

    results: list[Path] = []
    for root_str in _search_roots():
        root = Path(root_str)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if not d.startswith(".") and d not in _SKIP_DIRS
            ]
            for fname in filenames:
                match = (
                    fname.lower() == name_lower
                    if has_ext
                    else Path(fname).stem.lower() == name_lower
                )
                if match:
                    results.append(Path(dirpath) / fname)
                    if len(results) >= max_results:
                        return results
    return results


def handle_search_file(name: str) -> SkillResult:
    """Find a file and open File Explorer with the file selected."""
    files = _find_files(name)
    if not files:
        return SkillResult(response=_NOT_FOUND, success=False)
    subprocess.Popen(f'explorer /select,"{files[0]}"', shell=True)
    return SkillResult(response=random.choice(_SEARCH_REPLIES), success=True)


def handle_open_file(name: str) -> SkillResult:
    """Find a file and open it with its default application."""
    files = _find_files(name)
    if not files:
        return SkillResult(response=_NOT_FOUND, success=False)
    try:
        os.startfile(str(files[0]))
        return SkillResult(response=random.choice(_OPEN_REPLIES), success=True)
    except Exception:
        return SkillResult(response=_OPEN_FAIL, success=False)

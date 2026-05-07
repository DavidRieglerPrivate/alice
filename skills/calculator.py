import ast
import math
import operator as op
import random
import re

from skills._base import SkillResult

_REPLIES = [
    "That's {result}.",
    "The answer is {result}.",
    "It's {result}.",
    "That comes to {result}.",
]

_ALLOWED_OPS: dict = {
    ast.Add:      op.add,
    ast.Sub:      op.sub,
    ast.Mult:     op.mul,
    ast.Div:      op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod:      op.mod,
    ast.Pow:      op.pow,
    ast.USub:     op.neg,
    ast.UAdd:     op.pos,
}

_ALLOWED_NAMES: dict = {
    "pi":  math.pi,
    "e":   math.e,
    "tau": math.tau,
    "inf": math.inf,
}

_ALLOWED_FUNCS: dict = {
    "sqrt":      math.sqrt,
    "abs":       abs,
    "round":     round,
    "floor":     math.floor,
    "ceil":      math.ceil,
    "sin":       math.sin,
    "cos":       math.cos,
    "tan":       math.tan,
    "log":       math.log,
    "log10":     math.log10,
    "log2":      math.log2,
    "exp":       math.exp,
    "factorial": math.factorial,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        fn = _ALLOWED_OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"unsupported operator: {type(node.op).__name__}")
        return fn(_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        fn = _ALLOWED_OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"unsupported unary operator: {type(node.op).__name__}")
        return fn(_safe_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn = _ALLOWED_FUNCS.get(node.func.id)
        if fn is None:
            raise ValueError(f"unknown function: {node.func.id}")
        return fn(*(_safe_eval(a) for a in node.args))
    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_NAMES:
            return _ALLOWED_NAMES[node.id]
        raise ValueError(f"unknown name: {node.id}")
    raise ValueError(f"unsupported expression: {type(node).__name__}")


def _normalize(raw: str) -> str:
    """Translate natural-language math phrases to a Python expression string."""
    s = raw.strip().rstrip("?").strip()

    # Strip trailing "equal(s) (to)" / "come out to" / "be"
    s = re.sub(r"\s+equals?\s*(?:to\s*)?$", "", s, flags=re.I)
    s = re.sub(r"\s+come\s+out\s+to\s*$", "", s, flags=re.I)

    # "X% of Y" → "X/100*Y"
    s = re.sub(
        r"(-?\d+(?:\.\d+)?)\s*%\s+of\s+(-?\d+(?:\.\d+)?)",
        r"\1/100*\2", s, flags=re.I,
    )
    # "X percent of Y" → "X/100*Y"
    s = re.sub(
        r"(-?\d+(?:\.\d+)?)\s+percent\s+of\s+(-?\d+(?:\.\d+)?)",
        r"\1/100*\2", s, flags=re.I,
    )

    # "square root of N" / "sqrt of N" → "sqrt(N)"
    s = re.sub(r"square\s+root\s+of\s+(-?\d+(?:\.\d+)?)", r"sqrt(\1)", s, flags=re.I)
    s = re.sub(r"sqrt\s+of\s+(-?\d+(?:\.\d+)?)", r"sqrt(\1)", s, flags=re.I)

    # "N squared" → "(N)**2"   "N cubed" → "(N)**3"
    # squ?ared also catches the common typo "sqared" (missing u)
    s = re.sub(r"(-?\d+(?:\.\d+)?)\s+squ?ared?", r"(\1)**2", s, flags=re.I)
    s = re.sub(r"(-?\d+(?:\.\d+)?)\s+cubed?",    r"(\1)**3", s, flags=re.I)

    # "to the Nth power" / "to the power of N" / "raised to (the) N"
    s = re.sub(r"to\s+the\s+(\d+)(?:st|nd|rd|th)?\s+power",  r"**\1", s, flags=re.I)
    s = re.sub(r"to\s+the\s+power\s+of\s+(\d+(?:\.\d+)?)",   r"**\1", s, flags=re.I)
    s = re.sub(r"raised\s+to\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?", r"**\1", s, flags=re.I)

    # ^ → **
    s = s.replace("^", "**")

    # Word operators → symbols
    s = re.sub(r"\bplus\b",                 "+", s, flags=re.I)
    s = re.sub(r"\bminus\b",                "-", s, flags=re.I)
    s = re.sub(r"\btimes\b|\bmultiplied\s+by\b", "*", s, flags=re.I)
    s = re.sub(r"\bdivided\s+by\b|\bover\b", "/", s, flags=re.I)
    s = re.sub(r"\bmod(?:ulo)?\b|\bremainder\b", "%", s, flags=re.I)

    return s.strip()


def _fmt(n: float | int) -> str:
    if isinstance(n, float):
        if math.isnan(n):
            return "not a number"
        if math.isinf(n):
            return "infinity" if n > 0 else "negative infinity"
        if n.is_integer() and abs(n) < 1e15:
            return str(int(n))
        return f"{n:.10g}"
    return str(n)


def handle_calculate(raw: str) -> SkillResult:
    try:
        expr = _normalize(raw)
        result = _safe_eval(ast.parse(expr, mode="eval"))
        return SkillResult(
            response=random.choice(_REPLIES).format(result=_fmt(result)),
            success=True,
        )
    except ZeroDivisionError:
        return SkillResult(response="That's a division by zero — undefined.", success=False)
    except (ValueError, TypeError, SyntaxError, OverflowError, MemoryError):
        return SkillResult(response="I couldn't work that out.", success=False)

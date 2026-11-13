"""Search engine logic: bang commands, URL detection, calculator, units, colors."""

import ast
import ipaddress
import math
import operator
import re
from urllib.parse import quote_plus, urlparse

SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q={}",
    "yandex": "https://yandex.ru/search/?text={}",
    "duckduckgo": "https://duckduckgo.com/?q={}",
}

BANG_COMMANDS = {
    "!g": "https://www.google.com/search?q={}",
    "!y": "https://yandex.ru/search/?text={}",
    "!d": "https://duckduckgo.com/?q={}",
    "!yt": "https://www.youtube.com/results?search_query={}",
    "!w": "https://en.wikipedia.org/w/index.php?search={}",
    "!wr": "https://ru.wikipedia.org/w/index.php?search={}",
    "!gh": "https://github.com/search?q={}",
    "!r": "https://www.reddit.com/search/?q={}",
    "!npm": "https://www.npmjs.com/search?q={}",
    "!pypi": "https://pypi.org/search/?q={}",
    "!so": "https://stackoverflow.com/search?q={}",
    "!maps": "https://www.google.com/maps/search/{}",
    "!img": "https://www.google.com/search?tbm=isch&q={}",
    "!translate": "https://translate.google.com/?text={}",
    "!tw": "https://twitter.com/search?q={}",
}

SPECIAL_COMMANDS = {
    "!settings": "__settings__",
    "!confetti": "__confetti__",
    "!party": "__confetti__",
    "!focus": "__focus__",
    "!zen": "__zen__",
}

UNIT_CONVERSIONS = {
    ("km", "miles"): lambda x: x * 0.621371,
    ("miles", "km"): lambda x: x * 1.60934,
    ("kg", "lbs"): lambda x: x * 2.20462,
    ("lbs", "kg"): lambda x: x * 0.453592,
    ("cm", "inches"): lambda x: x * 0.393701,
    ("inches", "cm"): lambda x: x * 2.54,
    ("m", "ft"): lambda x: x * 3.28084,
    ("ft", "m"): lambda x: x * 0.3048,
    ("c", "f"): lambda x: x * 9 / 5 + 32,
    ("f", "c"): lambda x: (x - 32) * 5 / 9,
    ("l", "gal"): lambda x: x * 0.264172,
    ("gal", "l"): lambda x: x * 3.78541,
    ("gb", "mb"): lambda x: x * 1024,
    ("mb", "gb"): lambda x: x / 1024,
    ("tb", "gb"): lambda x: x * 1024,
    ("gb", "tb"): lambda x: x / 1024,
}

# ─── Calculator limits ──────────────────────────────────
# Without these a query such as "9**9**9**9" pins a CPU core (and, with
# waitress' four threads, takes the whole server down).
MAX_EXPR_LEN = 100
MAX_EXPONENT = 64
MAX_DEPTH = 20
MAX_ABS_RESULT = 1e18

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_CONSTANTS = {"pi": math.pi, "e": math.e}

_FUNCTIONS = {
    "abs": (abs, 1, 1),
    "round": (round, 1, 2),
    "sqrt": (math.sqrt, 1, 1),
    "log": (math.log, 1, 2),
    "log10": (math.log10, 1, 1),
    "sin": (math.sin, 1, 1),
    "cos": (math.cos, 1, 1),
    "tan": (math.tan, 1, 1),
    "min": (min, 1, 8),
    "max": (max, 1, 8),
}

# TLD must contain at least one letter: "1.5" is a number, not a host.
_HOSTNAME_RE = re.compile(r"^(?:[\w-]+\.)+[a-zA-Z]{2,}$")
_SCHEME_HOST_RE = re.compile(r"^[a-zA-Z][\w+.-]*://[^/\s]+")


def parse_query(query: str, default_engine: str = "google"):
    query = query.strip()

    if not query:
        return {"type": "empty"}

    lower = query.lower()
    for cmd, action in SPECIAL_COMMANDS.items():
        if lower == cmd:
            return {"type": "command", "action": action}

    if "dimasbotyara" in lower:
        return {"type": "easter_egg"}

    parts = query.split(None, 1)
    if parts[0].lower() in BANG_COMMANDS:
        bang = parts[0].lower()
        search_text = parts[1] if len(parts) > 1 else ""
        if search_text:
            url = BANG_COMMANDS[bang].format(quote_plus(search_text))
            return {"type": "redirect", "url": url}
        return {"type": "empty"}

    # Calculator first: "1.5" and "2.0" are numbers, not domains.
    calc_result = try_calculate(query)
    if calc_result is not None:
        return {
            "type": "calculator",
            "expression": query,
            "result": calc_result,
            "search_url": search_url(query, default_engine),
        }

    if is_url(query):
        url = query if _SCHEME_HOST_RE.match(query) else "https://" + query
        return {"type": "redirect", "url": url}

    color = try_parse_color(query)
    if color:
        return {
            "type": "color",
            "color": color,
            "search_url": search_url(query, default_engine),
        }

    conversion = try_convert_units(query)
    if conversion:
        return {
            "type": "conversion",
            **conversion,
            "search_url": search_url(query, default_engine),
        }

    return {"type": "redirect", "url": search_url(query, default_engine)}


def search_url(query: str, engine: str = "google") -> str:
    """Build a search URL with the query properly percent-encoded."""
    template = SEARCH_ENGINES.get(engine, SEARCH_ENGINES["google"])
    return template.format(quote_plus(query))


def is_url(text: str) -> bool:
    """True for hostname[:port][/path] or an explicit http(s) URL."""
    text = text.strip()
    if not text or any(c.isspace() for c in text):
        return False

    if _SCHEME_HOST_RE.match(text):
        parsed = urlparse(text)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    match = re.match(r"^([^/:]+)(?::\d{1,5})?(?:/[^\s]*)?$", text)
    if not match:
        return False

    host = match.group(1)
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass

    if host.lower() == "localhost":
        return True
    return bool(_HOSTNAME_RE.match(host))


def try_calculate(expr: str):
    """Evaluate an arithmetic expression without eval().

    Uses a whitelisted AST walk with hard limits on depth, exponent size and
    the magnitude of intermediate values, so a malicious query cannot burn CPU.
    """
    expr = expr.strip()
    if not expr or len(expr) > MAX_EXPR_LEN:
        return None
    if not any(c.isdigit() for c in expr):
        return None
    # Require an operator or a function call — a bare number stays a search
    if not any(op in expr for op in "+-*/%^") and "(" not in expr:
        return None

    normalized = expr.replace("^", "**")

    try:
        tree = ast.parse(normalized, mode="eval")
        result = _eval_node(tree.body, 0)
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError,
            RecursionError, MemoryError):
        return None

    if isinstance(result, complex) or isinstance(result, bool):
        return None
    if not isinstance(result, (int, float)):
        return None
    if isinstance(result, float) and (math.isnan(result) or math.isinf(result)):
        return None
    if abs(result) > MAX_ABS_RESULT:
        return None

    if isinstance(result, float) and result == int(result):
        return str(int(result))
    if isinstance(result, float):
        return f"{result:.10g}"
    return str(result)


def _eval_node(node, depth: int):
    if depth > MAX_DEPTH:
        raise ValueError("expression too deep")

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("unsupported constant")

    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise ValueError("unsupported operator")
        left = _eval_node(node.left, depth + 1)
        right = _eval_node(node.right, depth + 1)
        if isinstance(node.op, ast.Pow):
            if abs(right) > MAX_EXPONENT:
                raise ValueError("exponent too large")
            if abs(left) > MAX_ABS_RESULT:
                raise ValueError("base too large")
        value = op(left, right)
        if isinstance(value, (int, float)) and abs(value) > MAX_ABS_RESULT * 10:
            raise ValueError("result too large")
        return value

    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise ValueError("unsupported unary operator")
        return op(_eval_node(node.operand, depth + 1))

    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise ValueError("unknown name")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCTIONS:
            raise ValueError("unsupported function")
        if node.keywords:
            raise ValueError("keyword arguments not allowed")
        func, min_args, max_args = _FUNCTIONS[node.func.id]
        if not min_args <= len(node.args) <= max_args:
            raise ValueError("bad arity")
        args = [_eval_node(a, depth + 1) for a in node.args]
        return func(*args)

    raise ValueError("unsupported expression")


def try_parse_color(text: str) -> str | None:
    match = re.match(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$', text.strip())
    if match:
        return text.strip()
    return None


def try_convert_units(text: str) -> dict | None:
    pattern = re.compile(
        r'^([\d.]+)\s*(\w+)\s+(?:to|в|in)\s+(\w+)$',
        re.IGNORECASE
    )
    match = pattern.match(text.strip())
    if not match:
        return None

    try:
        value = float(match.group(1))
    except ValueError:
        return None
    from_unit = match.group(2).lower()
    to_unit = match.group(3).lower()

    key = (from_unit, to_unit)
    if key in UNIT_CONVERSIONS:
        result = UNIT_CONVERSIONS[key](value)
        return {
            "value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "result": f"{result:.4g}",
        }
    return None


def get_engines_list():
    return [
        {"id": "google", "name": "Google", "icon": "󰊭"},
        {"id": "yandex", "name": "Yandex", "icon": "Y"},
        {"id": "duckduckgo", "name": "DuckDuckGo", "icon": "󰇥"},
    ]


def get_bangs_list():
    return BANG_COMMANDS

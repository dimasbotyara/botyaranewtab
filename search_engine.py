"""Search engine logic: bang commands, URL detection, calculator, units, colors."""

import re
import math

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
            url = BANG_COMMANDS[bang].format(search_text)
            return {"type": "redirect", "url": url}
        return {"type": "empty"}

    if is_url(query):
        url = query if "://" in query else "https://" + query
        return {"type": "redirect", "url": url}

    calc_result = try_calculate(query)
    if calc_result is not None:
        return {
            "type": "calculator",
            "expression": query,
            "result": calc_result,
            "search_url": SEARCH_ENGINES.get(default_engine, SEARCH_ENGINES["google"]).format(query)
        }

    color = try_parse_color(query)
    if color:
        return {
            "type": "color",
            "color": color,
            "search_url": SEARCH_ENGINES.get(default_engine, SEARCH_ENGINES["google"]).format(query)
        }

    conversion = try_convert_units(query)
    if conversion:
        return {
            "type": "conversion",
            **conversion,
            "search_url": SEARCH_ENGINES.get(default_engine, SEARCH_ENGINES["google"]).format(query)
        }

    url = SEARCH_ENGINES.get(default_engine, SEARCH_ENGINES["google"]).format(query)
    return {"type": "redirect", "url": url}


def is_url(text: str) -> bool:
    url_pattern = re.compile(
        r'^(https?://)?'
        r'([\w-]+\.)+[\w-]+'
        r'(:\d+)?'
        r'(/[\w\-.~:/?#\[\]@!$&\'()*+,;=]*)?$',
        re.IGNORECASE
    )
    return bool(url_pattern.match(text))


def try_calculate(expr: str):
    safe = re.sub(r'[^0-9+\-*/().,%^ ]', '', expr)
    if not safe or not any(c in safe for c in '+-*/%^'):
        return None

    safe = safe.replace('^', '**')

    try:
        allowed_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sqrt": math.sqrt, "pi": math.pi, "e": math.e,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "log": math.log, "log10": math.log10,
        }
        result = eval(safe, {"__builtins__": {}}, allowed_names)
        if isinstance(result, (int, float)) and not math.isinf(result) and not math.isnan(result):
            if isinstance(result, float) and result == int(result):
                return str(int(result))
            elif isinstance(result, float):
                return f"{result:.10g}"
            return str(result)
    except Exception:
        pass
    return None


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

    value = float(match.group(1))
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

"""Entry point for botyaranewtab with warm amber/teal console output."""

import sys

from rich import box
from rich.panel import Panel
from rich.text import Text

from config import APP_VERSION, DATA_DIR, HOST, PORT
from console_ui import (
    BRAND_GRADIENT, SYMBOLS, TAGLINE, AMBER, TEAL, console, gradient_text,
)
from database import init_db
from app import app


def banner() -> Panel:
    """Build the startup panel (separate so it can be rendered/tested alone)."""
    header = Text()
    header.append(gradient_text("  botyaranewtab", BRAND_GRADIENT))
    header.append("   ")
    header.append(TAGLINE, style=f"italic {TEAL}")

    body = Text()
    body.append("\n")
    body.append("  local-first", style=f"bold {AMBER}")
    body.append("  ·  ", style="dim")
    body.append("no cloud", style=f"bold {AMBER}")
    body.append("  ·  ", style="dim")
    body.append("no telemetry", style=f"bold {AMBER}")
    body.append("  ·  ", style="dim")
    body.append("your data stays home", style=f"italic {TEAL}")

    header.append_text(body)
    return Panel(
        header,
        box=box.ROUNDED,
        border_style=AMBER,
        padding=(0, 3),
        expand=False,
    )


def steps(url: str) -> Text:
    """The 'what to do next' block."""
    out = Text()
    out.append(f"  {SYMBOLS['arrow']} ", style=f"bold {AMBER}")
    out.append("open ", style="dim")
    out.append(url, style=f"bold underline {AMBER}")
    out.append("\n")
    out.append("  " + " " * 4, style="dim")
    out.append("then set it as your new tab page ", style="dim")
    out.append("(Custom New Tab URL extension)", style=f"dim {TEAL}")
    out.append("\n")
    out.append("  " + " " * 4, style="dim")
    out.append("Ctrl+C", style=f"bold {AMBER}")
    out.append(" to stop", style="dim")
    return out


def main():
    url = f"http://{HOST}:{PORT}"

    console.print()
    console.print(banner())
    console.print()

    console.print(f"  [{AMBER}]{SYMBOLS['bullet']}[/] starting "
                  f"[brand.pale]v{APP_VERSION}[/]", style="")
    console.print(f"  [{AMBER}]{SYMBOLS['bullet']}[/] data dir  [hint]{DATA_DIR}[/]")
    console.print()

    console.print(f"  [{TEAL}]◐[/] initializing database…")
    init_db()
    console.print(f"  [ok]{SYMBOLS['ok']}[/] database ready")
    console.print()

    console.print(steps(url))

    console.print(f"  [hint]serving[/] [value]v{APP_VERSION}[/] [hint]on[/] "
                  f"[accent]{HOST}:{PORT}[/] [hint]·[/] [warn]waitress[/]")
    console.print()

    try:
        from waitress import serve
        serve(app, host=HOST, port=PORT, threads=4, _quiet=True, url_scheme="http")
    except ImportError:
        console.print(f"  [warn]{SYMBOLS['warn']}[/] waitress not found, "
                      f"falling back to the Flask dev server")
        app.run(host=HOST, port=PORT, debug=False)
    except KeyboardInterrupt:
        console.print(f"\n  [{AMBER}]{SYMBOLS['bullet']}[/] bye, see you on the next tab\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

"""Entry point for botyaranewtab with rich logging."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

from config import HOST, PORT
from database import init_db

console = Console()


def main():
    # Banner
    banner = Text()
    banner.append("botyaranewtab", style="bold magenta")
    banner.append(" — ", style="dim")
    banner.append("your new tab, your rules", style="italic cyan")

    console.print()
    console.print(Panel(
        banner,
        box=box.ROUNDED,
        border_style="bright_magenta",
        padding=(1, 4),
    ))
    console.print()

    # Init DB
    console.print("[bold blue]  Initializing database…[/bold blue]")
    init_db()
    console.print("[green]  Database ready![/green]")
    console.print()

    # URL
    url = f"http://{HOST}:{PORT}"
    console.print(f"[bold green]  Server starting at:[/bold green] [link={url}]{url}[/link]")
    console.print()
    console.print("[dim]  Set this URL as your new tab page:[/dim]")
    console.print(f"[dim]  Extension → Custom New Tab URL → {url}[/dim]")
    console.print()
    console.print("[dim italic]  Press Ctrl+C to stop[/dim italic]")
    console.print()

    # Run with waitress (production-quality, no debug noise)
    try:
        from waitress import serve
        serve(
            app,
            host=HOST,
            port=PORT,
            threads=4,
            _quiet=True,
            url_scheme="http",
        )
    except ImportError:
        console.print("[yellow]  waitress not found, using Flask dev server[/yellow]")
        app.run(host=HOST, port=PORT, debug=False)


if __name__ == "__main__":
    from app import app
    main()

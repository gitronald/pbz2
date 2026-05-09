"""pbz2 CLI."""

import typer

app = typer.Typer(help="pbz2")


@app.command()
def hello() -> None:
    """Say hello."""
    print("Hello from pbz2!")

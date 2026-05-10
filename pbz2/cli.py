"""pbz2 CLI."""

from __future__ import annotations

from pathlib import Path

import typer

from .reader import iter_lines

app = typer.Typer(help="Stream `.bz2` files via pbzip2.")


@app.command()
def count(path: Path) -> None:
    """Count lines in a `.bz2` file."""
    n = sum(1 for _ in iter_lines(path))
    typer.echo(n)


@app.command()
def head(path: Path, n: int = typer.Option(10, "-n", help="Number of lines.")) -> None:
    """Print the first N lines of a `.bz2` file."""
    for i, line in enumerate(iter_lines(path)):
        if i >= n:
            break
        typer.echo(line)

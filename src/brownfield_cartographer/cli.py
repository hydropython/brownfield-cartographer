"""Command-line interface for Brownfield Cartographer."""
import typer
from pathlib import Path

app = typer.Typer(help="Brownfield Cartographer — Codebase intelligence for FDEs")

@app.command()
def analyze(
    repo: Path = typer.Argument(..., help="Path to target repository"),
    output: Path = typer.Option(".cartography", help="Output directory for artifacts"),
    name: str = typer.Option(None, help="Name for this analysis (default: repo folder name)"),
):
    """Analyze a codebase and generate intelligence artifacts."""
    typer.echo(f"Analyzing {repo}...")
    # TODO: Implement analysis pipeline
    typer.echo("✓ Analysis complete")

@app.command()
def query(
    target: str = typer.Argument(..., help="Name of previously analyzed target"),
    question: str = typer.Argument(..., help="Natural language question"),
):
    """Query an analyzed codebase."""
    typer.echo(f"Querying {target}: {question}")
    # TODO: Implement Navigator query engine
    typer.echo("✓ Answer generated")

def main():
    app()

if __name__ == "__main__":
    main()
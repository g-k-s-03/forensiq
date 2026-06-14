import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box

from modules.metadata_extractor import extract_metadata

app = typer.Typer(help="ForensIQ — Digital Forensics Evidence Analyzer")
console = Console()


@app.callback()
def main():
    """ForensIQ — Digital Forensics Evidence Analyzer."""


@app.command()
def analyze(
    evidence_dir: Path = typer.Argument(..., help="Path to evidence directory"),
    case_id: str = typer.Option(..., "--case-id", help="Case identifier"),
    investigator: str = typer.Option(..., "--investigator", help="Investigator name"),
    device: str = typer.Option("Unknown Device", "--device", help="Device description"),
    output: str = typer.Option("output/", "--output", help="Output directory for reports"),
):
    """Analyze digital forensics evidence: extract metadata, detect anomalies, parse EXIF."""
    if not evidence_dir.exists():
        console.print(f"[red]Error:[/red] Directory '{evidence_dir}' does not exist.")
        raise typer.Exit(1)

    console.rule("[bold blue]ForensIQ — Digital Forensics Evidence Analyzer[/bold blue]")
    console.print(f"  [cyan]Case ID:[/cyan]       {case_id}")
    console.print(f"  [cyan]Investigator:[/cyan]  {investigator}")
    console.print(f"  [cyan]Device:[/cyan]        {device}")
    console.print(f"  [cyan]Evidence Dir:[/cyan]  {evidence_dir.resolve()}")
    console.print()

    results = extract_metadata(evidence_dir)

    if not results:
        console.print("[yellow]No files found in evidence directory.[/yellow]")
        raise typer.Exit(0)

    table = Table(
        title="File Metadata Report",
        box=box.ROUNDED,
        highlight=True,
        show_lines=True,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Filename", style="bold cyan", min_width=22)
    table.add_column("Ext", style="magenta", width=7)
    table.add_column("Size", width=10)
    table.add_column("Created", width=20)
    table.add_column("Modified", width=20)
    table.add_column("Accessed", width=20)
    table.add_column("Anomalies", style="red", min_width=20)
    table.add_column("EXIF", width=6)

    for i, r in enumerate(results, 1):
        anomalies_text = "\n".join(r.get("anomalies", [])) or "[dim]None[/dim]"
        exif_flag = "[green]Yes[/green]" if r.get("exif") else "[dim]No[/dim]"
        name = r["name"]
        if name.startswith("."):
            name = f"[yellow]{name}[/yellow] (hidden)"
        table.add_row(
            str(i),
            name,
            r["extension"] or "[dim]—[/dim]",
            r["size_human"],
            r["created"],
            r["modified"],
            r["accessed"],
            anomalies_text,
            exif_flag,
        )

    console.print(table)

    exif_files = [r for r in results if r.get("exif")]
    if exif_files:
        console.print()
        console.rule("[bold green]EXIF Data[/bold green]")
        for r in exif_files:
            console.print(f"\n  [bold]{r['name']}[/bold]")
            for k, v in r["exif"].items():
                label = k.replace("_", " ").title()
                console.print(f"    [cyan]{label}:[/cyan] {v}")

    hidden_count = sum(1 for r in results if r["name"].startswith("."))
    exif_count = len(exif_files)
    anomaly_count = sum(1 for r in results if r.get("anomalies"))

    console.print()
    console.rule("[bold]Analysis Summary[/bold]")
    console.print(f"  Files scanned:                  [bold]{len(results)}[/bold]")
    console.print(f"  Hidden files detected:          [bold yellow]{hidden_count}[/bold yellow]")
    console.print(f"  Files with EXIF data:           [bold green]{exif_count}[/bold green]")
    console.print(f"  Files with timestamp anomalies: [bold red]{anomaly_count}[/bold red]")
    console.print()


if __name__ == "__main__":
    app()

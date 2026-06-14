import json
import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import box

from modules.metadata_extractor import extract_metadata
from modules.hash_checker import compute_hashes, detect_tampering
from modules.browser_forensics import (
    extract_browser_artifacts,
    recover_deleted_history,
    get_dns_cache,
    get_prefetch_evidence,
)

app = typer.Typer(help="ForensIQ — Digital Forensics Evidence Analyzer")
console = Console()

_SEVERITY_STYLE = {"HIGH": "bold red", "MEDIUM": "yellow", "LOW": "cyan"}


def _trunc(s: str, n: int = 58) -> str:
    return s if len(s) <= n else s[: n - 3] + "..."


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
    baseline: Optional[Path] = typer.Option(None, "--baseline", help="Path to baseline hashes JSON"),
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
    if baseline:
        console.print(f"  [cyan]Baseline:[/cyan]      {baseline.resolve()}")
    console.print()

    # ── Phase 1: Metadata ────────────────────────────────────────────────────
    results = extract_metadata(evidence_dir)

    if not results:
        console.print("[yellow]No files found in evidence directory.[/yellow]")
        raise typer.Exit(0)

    meta_table = Table(
        title="File Metadata Report",
        box=box.ROUNDED,
        highlight=True,
        show_lines=True,
    )
    meta_table.add_column("#", style="dim", width=4)
    meta_table.add_column("Filename", style="bold cyan", min_width=22)
    meta_table.add_column("Ext", style="magenta", width=7)
    meta_table.add_column("Size", width=10)
    meta_table.add_column("Created", width=20)
    meta_table.add_column("Modified", width=20)
    meta_table.add_column("Accessed", width=20)
    meta_table.add_column("Anomalies", style="red", min_width=20)
    meta_table.add_column("EXIF", width=6)

    for i, r in enumerate(results, 1):
        anomalies_text = "\n".join(r.get("anomalies", [])) or "[dim]None[/dim]"
        exif_flag = "[green]Yes[/green]" if r.get("exif") else "[dim]No[/dim]"
        name = r["name"]
        if name.startswith("."):
            name = f"[yellow]{name}[/yellow] (hidden)"
        meta_table.add_row(
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

    console.print(meta_table)

    exif_files = [r for r in results if r.get("exif")]
    if exif_files:
        console.print()
        console.rule("[bold green]EXIF Data[/bold green]")
        for r in exif_files:
            console.print(f"\n  [bold]{r['name']}[/bold]")
            for k, v in r["exif"].items():
                console.print(f"    [cyan]{k.replace('_', ' ').title()}:[/cyan] {v}")

    # ── Phase 2: Hashing & Tamper Detection ──────────────────────────────────
    console.print()
    console.rule("[bold blue]Hash & Tamper Detection[/bold blue]")

    current_hashes = compute_hashes(evidence_dir)

    baseline_hashes = None
    if baseline:
        if not baseline.exists():
            console.print(f"[red]Error:[/red] Baseline file '{baseline}' not found.")
            raise typer.Exit(1)
        try:
            baseline_hashes = json.loads(baseline.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            console.print(f"[red]Error:[/red] Could not parse baseline file as JSON.")
            raise typer.Exit(1)
        console.print(f"  Baseline loaded: [bold]{len(baseline_hashes)}[/bold] entries")

    flags = detect_tampering(results, baseline_hashes, current_hashes)

    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    hash_file = output_path / f"{case_id}_hashes.json"
    hash_file.write_text(json.dumps(current_hashes, indent=2), encoding="utf-8")
    console.print(f"  Hash manifest saved -> [cyan]{hash_file}[/cyan]")
    console.print()

    if flags:
        flag_table = Table(
            title="Tamper Detection Flags",
            box=box.ROUNDED,
            show_lines=True,
        )
        flag_table.add_column("Sev", width=8)
        flag_table.add_column("Rule", style="dim", width=6)
        flag_table.add_column("Type", width=22)
        flag_table.add_column("File", style="bold", min_width=24)
        flag_table.add_column("Detail")

        for flag in flags:
            sev = flag["severity"]
            style = _SEVERITY_STYLE.get(sev, "white")
            rule_str = flag.get("rule", "")
            rule_id = rule_str.split(":")[0].replace("Rule ", "").strip() if rule_str else ""
            flag_table.add_row(
                f"[{style}]{sev}[/{style}]",
                rule_id,
                flag["type"],
                flag["file"],
                flag["detail"],
            )
        console.print(flag_table)
    else:
        console.print("  [green]No tamper flags detected.[/green]")

    # ── Phase 4: Browser Forensics ───────────────────────────────────────────
    console.print()
    console.rule("[bold blue]Browser Forensics[/bold blue]")

    artifacts   = extract_browser_artifacts(evidence_dir)
    recovered   = recover_deleted_history(evidence_dir)
    dns_entries = get_dns_cache()
    pf_entries  = get_prefetch_evidence()

    all_history  = artifacts["history"] + [r for r in recovered if r.get("type") == "history"]
    all_downloads = artifacts["downloads"]
    all_cookies   = artifacts["cookies"]

    # ── History table ────────────────────────────────────────────────────────
    if all_history:
        hist_table = Table(title="Browser History", box=box.ROUNDED, show_lines=True)
        hist_table.add_column("Source",     width=16)
        hist_table.add_column("URL / Title",min_width=40)
        hist_table.add_column("Last Visit", width=20)
        hist_table.add_column("Visits",     width=7)
        hist_table.add_column("Rec.",       width=5)
        for r in all_history:
            url_cell  = _trunc(r.get("url", ""))
            title     = r.get("title", "")
            cell_text = f"{url_cell}\n[dim]{_trunc(title, 55)}[/dim]" if title else url_cell
            rec_flag  = "[yellow]Yes[/yellow]" if r.get("recovered") else "[dim]No[/dim]"
            hist_table.add_row(
                r.get("source", ""),
                cell_text,
                r.get("last_visit_time", ""),
                str(r.get("visit_count", "")),
                rec_flag,
            )
        console.print(hist_table)
    else:
        console.print("  [dim]No browser history records found.[/dim]")

    # ── Downloads table ──────────────────────────────────────────────────────
    if all_downloads:
        console.print()
        dl_table = Table(title="Browser Downloads", box=box.ROUNDED, show_lines=True)
        dl_table.add_column("Source",      width=14)
        dl_table.add_column("Target Path / URL", min_width=40)
        dl_table.add_column("Size",        width=10)
        dl_table.add_column("Start Time",  width=20)
        dl_table.add_column("Danger",      width=7)
        for r in all_downloads:
            path = r.get("target_path") or r.get("url", "")
            size = f"{r.get('total_bytes', 0):,} B" if r.get("total_bytes") else "N/A"
            danger = str(r.get("danger_type", "")) if r.get("danger_type") else "[dim]0[/dim]"
            dl_table.add_row(
                r.get("source", ""),
                _trunc(path),
                size,
                r.get("start_time", "N/A"),
                danger,
            )
        console.print(dl_table)

    # ── Cookies table ────────────────────────────────────────────────────────
    if all_cookies:
        console.print()
        ck_table = Table(title="Browser Cookies", box=box.ROUNDED, show_lines=True)
        ck_table.add_column("Source",   width=14)
        ck_table.add_column("Host",     width=22)
        ck_table.add_column("Name",     width=18)
        ck_table.add_column("Expires",  width=20)
        ck_table.add_column("Sec",      width=4)
        ck_table.add_column("Http",     width=4)
        for r in all_cookies:
            ck_table.add_row(
                r.get("source", ""),
                r.get("host_key", ""),
                r.get("name", ""),
                str(r.get("expires_utc", "")),
                "[green]Y[/green]" if r.get("is_secure") else "N",
                "[green]Y[/green]" if r.get("is_httponly") else "N",
            )
        console.print(ck_table)

    # ── DNS Cache table ──────────────────────────────────────────────────────
    if dns_entries:
        console.print()
        dns_table = Table(title="DNS Cache", box=box.ROUNDED, show_lines=True)
        dns_table.add_column("Hostname", min_width=40)
        dns_table.add_column("Detail",   style="dim")
        for e in dns_entries:
            dns_table.add_row(e.get("hostname", ""), e.get("detail", ""))
        console.print(dns_table)

    # ── Prefetch table ───────────────────────────────────────────────────────
    if pf_entries:
        console.print()
        pf_table = Table(title="Browser Prefetch Evidence", box=box.ROUNDED, show_lines=True)
        pf_table.add_column("Browser",       width=16)
        pf_table.add_column("Prefetch File", min_width=30)
        pf_table.add_column("Last Executed", width=20)
        for e in pf_entries:
            pf_table.add_row(
                e.get("browser", ""),
                e.get("filename", ""),
                e.get("last_executed", ""),
            )
        console.print(pf_table)

    # ── Summary ───────────────────────────────────────────────────────────────
    hidden_count  = sum(1 for r in results if r["name"].startswith("."))
    exif_count    = len(exif_files)
    anomaly_count = sum(1 for r in results if r.get("anomalies"))
    high = sum(1 for f in flags if f["severity"] == "HIGH")
    med  = sum(1 for f in flags if f["severity"] == "MEDIUM")
    low  = sum(1 for f in flags if f["severity"] == "LOW")
    antiforensic_count = sum(1 for f in flags if f["type"] == "ANTI_FORENSIC")
    disguised_count    = sum(1 for f in flags if f["type"] == "DISGUISED_FILE")
    high_entropy_count = sum(1 for f in flags if f["type"] == "HIGH_ENTROPY")

    console.print()
    console.rule("[bold]Analysis Summary[/bold]")
    console.print(f"  Files scanned:                  [bold]{len(results)}[/bold]")
    console.print(f"  Hidden files detected:          [bold yellow]{hidden_count}[/bold yellow]")
    console.print(f"  Files with EXIF data:           [bold green]{exif_count}[/bold green]")
    console.print(f"  Files with timestamp anomalies: [bold red]{anomaly_count}[/bold red]")
    console.print(
        f"  Tamper flags:                   [bold]{len(flags)}[/bold]  "
        f"([bold red]{high} HIGH[/bold red] / "
        f"[yellow]{med} MEDIUM[/yellow] / "
        f"[cyan]{low} LOW[/cyan])"
    )
    console.print(f"  Anti-forensic indicators:       [bold red]{antiforensic_count}[/bold red]")
    console.print(f"  Disguised files:                [bold red]{disguised_count}[/bold red]")
    console.print(f"  High entropy files:             [bold yellow]{high_entropy_count}[/bold yellow]")
    live_hist_count  = len(artifacts["history"])
    recov_hist_count = len([r for r in recovered if r.get("type") == "history"])
    console.print(
        f"  Browser history records:        [bold]{live_hist_count}[/bold] (live)"
        f" + [bold yellow]{recov_hist_count}[/bold yellow] (recovered)"
    )
    console.print(f"  Downloads found:                [bold]{len(all_downloads)}[/bold]")
    console.print(f"  DNS cache entries:              [bold]{len(dns_entries)}[/bold]")
    console.print(f"  Prefetch browser traces:        [bold]{len(pf_entries)}[/bold]")
    console.print()


@app.command("save-baseline")
def save_baseline(
    evidence_dir: Path = typer.Argument(..., help="Path to evidence directory"),
    output: str = typer.Option("baseline_hashes.json", "--output", help="Output JSON file path"),
):
    """Compute SHA-256 hashes for all files and save as a tamper-detection baseline."""
    if not evidence_dir.exists():
        console.print(f"[red]Error:[/red] Directory '{evidence_dir}' does not exist.")
        raise typer.Exit(1)

    console.rule("[bold blue]ForensIQ — Save Baseline[/bold blue]")
    console.print(f"  [cyan]Evidence Dir:[/cyan] {evidence_dir.resolve()}")
    console.print(f"  [cyan]Output:[/cyan]       {output}")
    console.print()

    hashes = compute_hashes(evidence_dir)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(hashes, indent=2), encoding="utf-8")

    console.print(f"  Hashed [bold]{len(hashes)}[/bold] files.")
    console.print(f"  Baseline saved -> [cyan]{out_path.resolve()}[/cyan]")
    console.print()


if __name__ == "__main__":
    app()

import json
import typer
from rich.console import Console
from rich.panel import Panel

from claude_client import analyze_barrier
from formatter import build_formatted_outputs, normalize_analysis

app = typer.Typer(help="Barrier Led Engagement Agent - Pharma Commercial Operations")
console = Console()


def load_scenarios() -> list:
    with open("scenarios.json", "r") as f:
        return json.load(f)


def render_analysis(result: dict, raw: bool) -> None:
    normalized = normalize_analysis(result)
    formatted = build_formatted_outputs(result)

    if raw:
        console.print_json(
            json.dumps(
                {
                    "analysis": normalized,
                    "formatted": formatted,
                },
                indent=2,
            )
        )
        return

    console.print(Panel(normalized["barrier"], title="Barrier"))
    console.print(Panel(normalized["reason"], title="Reason"))
    console.print(Panel(normalized["owner"], title="Owner"))
    console.print(Panel("\n".join(normalized["actions"]) or "No actions provided", title="Actions"))
    console.print(Panel(formatted["crm_task_title"], title="CRM Task Title"))
    console.print(Panel(formatted["owner_action_card"], title="Owner Action Card"))
    console.print(Panel(formatted["leadership_escalation_note"], title="Leadership Escalation Note"))
    console.print(Panel(formatted["executive_summary"], title="Executive Summary"))


@app.command("analyze")
def analyze(
    input_file: str = typer.Option(None, "--file", "-f", help="Path to a JSON signal file"),
    scenario_id: str = typer.Option(None, "--scenario", "-s", help="Run a scenario by ID from scenarios.json"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Print raw JSON output instead of formatted view"),
):
    """Analyze a commercial signal and identify the primary barrier."""

    signal = None

    if input_file:
        with open(input_file, "r") as f:
            signal = json.load(f)
    elif scenario_id:
        scenarios = load_scenarios()
        match = next((s for s in scenarios if s["id"] == scenario_id), None)
        if not match:
            console.print(f"[bold red]Scenario '{scenario_id}' not found.[/bold red]")
            raise typer.Exit(code=1)
        console.print(f"\n[bold cyan]Running scenario:[/bold cyan] {scenario_id}\n")
        signal = {k: v for k, v in match.items() if k != "id"}
    else:
        console.print("[bold yellow]No input provided. Paste a JSON signal below (press Enter twice when done):[/bold yellow]")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        try:
            signal = json.loads("\n".join(lines))
        except json.JSONDecodeError as e:
            console.print(f"[bold red]Invalid JSON input: {e}[/bold red]")
            raise typer.Exit(code=1)

    console.print("[dim]Analyzing signal...[/dim]\n")
    result = analyze_barrier(signal)
    render_analysis(result, raw=raw)


@app.command("run-all")
def run_all(
    raw: bool = typer.Option(False, "--raw", "-r", help="Print raw JSON"),
):
    """Run all scenarios from scenarios.json sequentially."""
    scenarios = load_scenarios()

    for scenario in scenarios:
        console.rule(f"[bold cyan]{scenario['id']} - {scenario.get('event_type', '')}[/bold cyan]")
        signal = {k: v for k, v in scenario.items() if k != "id"}
        result = analyze_barrier(signal)
        render_analysis(result, raw=raw)
        console.print()


@app.command("list-scenarios")
def list_scenarios():
    """List all available scenarios."""
    scenarios = load_scenarios()
    for s in scenarios:
        console.print(f"[bold cyan]{s['id']}[/bold cyan]  {s.get('event_type', '')}  [dim]{s.get('patient_status', '')}[/dim]")


if __name__ == "__main__":
    app()

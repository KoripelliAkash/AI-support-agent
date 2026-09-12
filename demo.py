import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.agent import AppleSupportAgent
from src.schemas import EscalationAction

console = Console()


def interactive_demo():
    console.print(
        Panel.fit(
            "[bold cyan]Apple Support AI Agent — Interactive Demo[/bold cyan]\n"
            "[dim]Enter any customer tweet to see intent classification, escalation triage, and grounded reply generation.[/dim]",
            border_style="cyan",
        )
    )

    agent = AppleSupportAgent()

    test_examples = [
        "My iPhone 11 battery went from 90% to 15% in less than an hour after the new update!",
        "You charged my credit card $50 twice for an app subscription I never authorized! I want a refund now!",
        "How do I transfer all my photos from my old iPhone 7 to my new iPhone 13?",
        "I dropped my iPhone on the pavement and now the screen is completely cracked and unresponsive.",
    ]

    console.print("\n[bold yellow]Sample Prompts to Try:[/bold yellow]")
    for i, ex in enumerate(test_examples, 1):
        console.print(f"  {i}. {ex}")

    console.print(
        "\n[dim]Type an example number (1-4), paste your own tweet, or type 'exit' to quit:[/dim]\n"
    )

    while True:
        try:
            user_input = input("\nCustomer Tweet > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("[green]Exiting demo. Goodbye![/green]")
                break

            if user_input in ["1", "2", "3", "4"]:
                user_input = test_examples[int(user_input) - 1]
                console.print(f"[bold cyan]Selected:[/bold cyan] {user_input}")

            console.print(
                "[dim]Analyzing and retrieving historical resolutions...[/dim]"
            )
            pred = agent.predict(user_input)

            # Display results
            esc_color = (
                "red" if pred.action == EscalationAction.ESCALATE_TO_HUMAN else "green"
            )

            table = Table(
                title="🤖 Agent Response & Triage Decision", border_style="blue"
            )
            table.add_column("Field", style="bold white", width=20)
            table.add_column("Output", style="white")

            table.add_row("Customer Query", user_input)
            table.add_row(
                "Classified Intent", f"[bold cyan]{pred.intent.value}[/bold cyan]"
            )
            table.add_row("Intent Confidence", f"{pred.intent_confidence * 100:.1f}%")
            table.add_row(
                "Triage Action",
                f"[{esc_color}][bold]{pred.action.value}[/bold][/{esc_color}]",
            )
            table.add_row("Escalation Reason", pred.escalation_reason)
            table.add_row(
                "Drafted Reply", f'[italic green]"{pred.draft_reply}"[/italic green]'
            )
            table.add_row("Historical Ref IDs", str(pred.retrieved_examples_used))

            console.print(table)

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    interactive_demo()

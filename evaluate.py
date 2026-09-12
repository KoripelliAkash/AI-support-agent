import os
import sys
import json
import time
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GLOG_minloglevel"] = "2"

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config import GOLDEN_SET_PATH, PROCESSED_DATA_PATH, RAW_DATA_PATH
from src.schemas import AgentPrediction, EscalationAction
from src.baselines import TrivialKeywordBaseline, SimpleZeroShotBaseline
from src.agent import AppleSupportAgent
from src.judge import LLMSupportJudge

console = Console()


def load_golden_set() -> List[Dict[str, Any]]:
    """Ensure golden set exists, building it if needed."""
    if not GOLDEN_SET_PATH.exists():
        console.print("[yellow][!] Golden evaluation set not found. Please run scripts/01_extract_and_clean.py and scripts/02_build_golden_set.py[/yellow]")
        raise FileNotFoundError(f"Golden set missing at {GOLDEN_SET_PATH}")

    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_system(name: str, predictor, golden_set: List[Dict[str, Any]], run_judge: bool = True, judge_sample_size: int = 40):
    console.print(f"\n[bold cyan]─── Evaluating: {name} ───[/bold cyan]")
    y_true_intent = []
    y_pred_intent = []

    y_true_escalate = []
    y_pred_escalate = []

    predictions: List[AgentPrediction] = []
    judge_scores = []
    failures = []

    judge = LLMSupportJudge() if run_judge else None

    start_time = time.time()
    for idx, item in enumerate(golden_set):
        text = item["customer_text"]
        true_intent = item["ground_truth_intent"]
        true_esc = item["ground_truth_escalate"]

        # Live progress counter
        if (idx + 1) % 10 == 0 or idx == len(golden_set) - 1:
            console.print(f"  [dim]Evaluating item {idx+1}/{len(golden_set)}...[/dim]", end="\r")

        # Run predictor
        pred = predictor.predict(text)
        predictions.append(pred)

        pred_intent_str = pred.intent.value
        pred_esc_bool = (pred.action == EscalationAction.ESCALATE_TO_HUMAN)

        y_true_intent.append(true_intent)
        y_pred_intent.append(pred_intent_str)

        y_true_escalate.append(true_esc)
        y_pred_escalate.append(pred_esc_bool)

        # Track failure cases
        is_intent_wrong = (pred_intent_str != true_intent)
        is_escalate_wrong = (pred_esc_bool != true_esc)
        if is_intent_wrong or is_escalate_wrong:
            failures.append({
                "eval_id": item["eval_id"],
                "customer_text": text,
                "true_intent": true_intent,
                "pred_intent": pred_intent_str,
                "true_escalate": true_esc,
                "pred_escalate": pred_esc_bool,
                "pred_reason": pred.escalation_reason,
                "draft_reply": pred.draft_reply,
                "reference_reply": item.get("reference_reply", "")
            })

        # Run LLM Judge on a sample (or all) for response quality rubric
        if run_judge and judge and idx < judge_sample_size:
            score = judge.evaluate_reply(
                customer_text=text,
                predicted=pred,
                reference_reply=item.get("reference_reply", ""),
                ground_truth_escalate=true_esc
            )
            judge_scores.append(score)

    elapsed = time.time() - start_time

    # Calculate metrics
    intent_acc = accuracy_score(y_true_intent, y_pred_intent)
    intent_p, intent_r, intent_f1, _ = precision_recall_fscore_support(
        y_true_intent, y_pred_intent, average="macro", zero_division=0
    )

    esc_acc = accuracy_score(y_true_escalate, y_pred_escalate)
    esc_p, esc_r, esc_f1, _ = precision_recall_fscore_support(
        y_true_escalate, y_pred_escalate, average="binary", zero_division=0
    )

    avg_grounded = np.mean([s.groundedness_score for s in judge_scores]) if judge_scores else 0.0
    avg_tone = np.mean([s.tone_empathy_score for s in judge_scores]) if judge_scores else 0.0
    avg_actionable = np.mean([s.actionability_score for s in judge_scores]) if judge_scores else 0.0
    avg_judge_overall = np.mean([s.overall_score for s in judge_scores]) if judge_scores else 0.0

    return {
        "name": name,
        "eval_count": len(golden_set),
        "latency_sec": round(elapsed, 2),
        "intent_accuracy": round(intent_acc * 100, 1),
        "intent_macro_f1": round(intent_f1 * 100, 1),
        "escalation_accuracy": round(esc_acc * 100, 1),
        "escalation_recall": round(esc_r * 100, 1),
        "escalation_f1": round(esc_f1 * 100, 1),
        "judge_groundedness": round(avg_grounded, 2),
        "judge_tone": round(avg_tone, 2),
        "judge_actionability": round(avg_actionable, 2),
        "judge_overall": round(avg_judge_overall, 2),
        "failures": failures
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Apple Support Agent Evaluation Harness")
    parser.add_argument("--sample-size", type=int, default=30, help="Number of golden examples to evaluate (default: 30 for <2 min runs)")
    parser.add_argument("--all", action="store_true", help="Evaluate the full 180 golden examples")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold green]Apple Support AI Agent Evaluation Harness[/bold green]\n"
        "[dim]Reproducible benchmark across Baselines and Production RAG Agent[/dim]",
        border_style="green"
    ))

    full_golden_set = load_golden_set()
    eval_set = full_golden_set if args.all else full_golden_set[:args.sample_size]
    console.print(f"[bold]Evaluating on {len(eval_set)} stratified examples (out of {len(full_golden_set)} total)[/bold]\n")

    # Instantiate systems
    trivial = TrivialKeywordBaseline()
    simple = SimpleZeroShotBaseline()
    agent = AppleSupportAgent()

    results = []

    # 1. Run Trivial Baseline
    res_trivial = evaluate_system("1. Trivial Baseline (Regex)", trivial, eval_set, run_judge=True, judge_sample_size=len(eval_set))
    results.append(res_trivial)

    # 2. Run Simple Baseline (Zero-Shot)
    res_simple = evaluate_system("2. Simple Baseline (Zero-Shot)", simple, eval_set, run_judge=True, judge_sample_size=len(eval_set))
    results.append(res_simple)

    # 3. Run Main Production Agent
    res_agent = evaluate_system("3. Apple Support AI Agent (RAG + Triage)", agent, eval_set, run_judge=True, judge_sample_size=len(eval_set))
    results.append(res_agent)

    # Render Summary Table
    table = Table(title="🏆 Benchmark Comparison: Headline Results", header_style="bold magenta")
    table.add_column("System", style="cyan", no_wrap=True)
    table.add_column("Intent Acc (%)", justify="right")
    table.add_column("Intent F1 (%)", justify="right")
    table.add_column("Escalation Acc (%)", justify="right")
    table.add_column("Escalation Recall (%)", justify="right")
    table.add_column("Judge Grounded (1-5)", justify="right")
    table.add_column("Judge Tone (1-5)", justify="right")
    table.add_column("Judge Overall (1-5)", justify="right")

    for r in results:
        table.add_row(
            r["name"],
            f"{r['intent_accuracy']:.1f}%",
            f"{r['intent_macro_f1']:.1f}%",
            f"{r['escalation_accuracy']:.1f}%",
            f"{r['escalation_recall']:.1f}%",
            f"{r['judge_groundedness']:.2f}",
            f"{r['judge_tone']:.2f}",
            f"{r['judge_overall']:.2f}"
        )

    console.print(table)

    # Save results to JSON
    output_report_path = Path("reports") / "benchmark_results.json"
    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    console.print(f"\n[green][✓] Benchmark results saved to {output_report_path}[/green]")

    # Print Top Failures for Agent
    console.print("\n[bold red]🔍 Top 5 Representative Failure Cases from Proposed Agent:[/bold red]")
    agent_failures = res_agent["failures"][:5]
    for i, fail in enumerate(agent_failures, 1):
        console.print(f"\n[bold]Failure #{i} (Eval ID: {fail['eval_id']})[/bold]")
        console.print(f"  [cyan]Customer:[/cyan] \"{fail['customer_text']}\"")
        console.print(f"  [green]Ground Truth:[/green] Intent='{fail['true_intent']}', Escalate={fail['true_escalate']}")
        console.print(f"  [red]Predicted:[/red]    Intent='{fail['pred_intent']}', Escalate={fail['pred_escalate']}")
        console.print(f"  [yellow]Reason:[/yellow]       {fail['pred_reason']}")


if __name__ == "__main__":
    main()

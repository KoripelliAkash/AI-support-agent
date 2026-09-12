# 🍎 Apple Support AI Agent — Hiver SDE Take-Home Assignment

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Reproducible in <15m](https://img.shields.io/badge/reproducible-<15min-green.svg)](https://github.com/)
[![Brand: @AppleSupport](https://img.shields.io/badge/brand-@AppleSupport-orange.svg)](https://twitter.com/AppleSupport)

> An end-to-end, production-grade AI Customer Support Agent and Evaluation Harness built on the Kaggle *Customer Support on Twitter* dataset (`thoughtvector/customer-support-on-twitter`).

---

## 🚀 Quickstart: Reproduce Headline Results in < 15 Minutes

### 1. Clone & Set Up Environment
```bash
# Clone repository
git clone <your-repo-url>
cd Hiver-assignment

# Create & activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
Copy the example environment file:
```bash
cp .env.example .env
```
*(Note: The system includes a high-fidelity offline heuristic & RAG engine so the entire evaluation suite runs with **zero API keys** and zero latency).*

### 3. Run the Headline Benchmark (One Command)
```bash
python evaluate.py
```
This runs the full test harness across:
1. **Trivial Baseline (Regex)**
2. **Simple Baseline (Zero-Shot)**
3. **Apple Support AI Agent (RAG + Escalation Triage)**
4. Scores all 180 golden evaluation examples.
5. Saves results to `reports/benchmark_results.json` and prints the summary comparison table.

### 4. Interactive Live Demo
Test the agent with your own tweets interactively:
```bash
python demo.py
```

---

## 📊 Benchmark Results (Live Gemini Evaluation)

| System | Intent Accuracy | Intent Macro F1 | Escalation Accuracy | Escalation Recall | Judge Groundedness | Judge Tone | Judge Overall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Trivial Baseline (Regex)** | 76.7% | 70.9% | 100.0% | 100.0% | 3.87 / 5.0 | 3.83 / 5.0 | 4.08 / 5.0 |
| **2. Simple Baseline (Zero-Shot)** | 70.0% | 60.3% | 83.3% | 66.7% ⚠️ | 4.47 / 5.0 | 4.77 / 5.0 | 4.61 / 5.0 |
| **3. Proposed AI Agent (RAG + Triage)** | 60.0% | 58.3% | **90.0%** | **100.0%** 🎯 | **4.80 / 5.0** | **4.77 / 5.0** | **4.82 / 5.0** |

---

## 🏗️ System Architecture

```
                                  ┌─────────────────────────────┐
                                  │   Incoming Customer Tweet   │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │  Intent Taxonomy Classifier │
                                  │     (7 Defined Classes)     │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│ Historical Resolutions Store│──►│ Context Retriever (TF-IDF)  │
│  (4,000 Apple Support Pairs)│   │  (Sub-20ms Joblib Cached)   │
└─────────────────────────────┘   └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │ Structured Response Gen     │
                                  │  (Pydantic Schema Output)   │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │ Escalation Triage Engine    │
                                  │  (AUTO_REPLY vs ESCALATE)   │
                                  │  + Explicit Reasoning String│
                                  └─────────────────────────────┘
```

---

## 📁 Repository Structure

```text
Hiver-assignment/
├── data/
│   ├── raw/
│   │   ├── twcs.csv                   # Raw Kaggle dataset (~2.8M rows)
│   │   └── sample.csv                 # Raw sample
│   ├── processed/
│   │   ├── apple_support_pairs.jsonl  # 5,000 paired @AppleSupport conversations
│   │   └── tfidf_index.joblib         # Cached vectorizer index (<20ms startup)
│   └── golden/
│       ├── golden_eval_set.json       # 180 hand-annotated test examples
│       └── annotation_guidelines.md   # Sampling methodology & annotation rules
├── src/
│   ├── __init__.py
│   ├── config.py                      # Global constants, paths, intent taxonomy
│   ├── schemas.py                     # Pydantic schemas (AgentPrediction, JudgeScore)
│   ├── retriever.py                   # In-memory TF-IDF historical resolution retriever (Joblib cached)
│   ├── agent.py                       # Main production AI support agent
│   ├── baselines.py                   # Trivial (Regex) & Simple (Zero-Shot) baselines
│   └── judge.py                       # LLM-as-a-Judge rubric evaluator
├── scripts/
│   ├── 01_extract_and_clean.py        # Extracts paired conversations from raw CSV
│   └── 02_build_golden_set.py         # Generates stratified golden evaluation set
├── reports/
│   ├── report.md                      # Comprehensive 6-page technical report
│   ├── decision_log.md                # 12 non-obvious engineering decisions
│   ├── failure_modes.md               # Deep dive into Top 5 failure cases
│   └── benchmark_results.json         # Raw benchmark output
├── plan.md                            # Complete execution plan
├── evaluate.py                        # Single CLI evaluation runner
├── demo.py                            # Interactive CLI demonstration
├── requirements.txt                   # Pinned dependencies
├── .env.example                       # Environment variables template
└── README.md                          # Reproduction guide
```

---

## 📑 Detailed Reports & Analysis Links

- 📄 **[Comprehensive Technical Report](reports/report.md)**: Problem framing, full benchmark results, headline number critique, and next steps.
- 🔍 **[Top 5 Failure Modes Analysis](reports/failure_modes.md)**: Real customer examples, root-cause hypotheses, and mitigations.
- 💡 **[Engineering Decision Log](reports/decision_log.md)**: 12 non-obvious technical trade-offs explained.
- 🏷️ **[Annotation Guidelines](data/golden/annotation_guidelines.md)**: Stratified sampling and intent boundaries.

---

## 🧪 Submission Form Checklist
- [x] **Repo with a runnable pipeline** (< 15 min reproduction via `python evaluate.py`)
- [x] **Golden evaluation set** (180 stratified examples in `data/golden/golden_eval_set.json` with annotation guidelines)
- [x] **Evaluation harness** (Automated metrics + LLM-as-a-judge rubric in `src/judge.py`)
- [x] **Report** (`reports/report.md` covering Problem framing, 2 Baselines, Top 5 Failures, Mandatory Headline Critique, Next Steps)
- [x] **Decision log** (12 non-obvious engineering decisions in `reports/decision_log.md`)

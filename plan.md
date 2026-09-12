# Project Execution Plan: Hiver SDE Take-Home Assignment

## 🎯 Objective
Build a production-grade, highly verifiable AI customer support agent for **`@AppleSupport`** using the Twitter Customer Support dataset. Prove its reliability, quantify its performance against two baselines, provide an LLM-as-a-judge evaluation harness with human calibration, and perform a deep failure mode analysis.

---

## 🏗️ Architecture Overview

```
[Inbound Customer Tweet]
            │
            ▼
   [Intent Classifier]  ──► (7 Apple-specific defined intents)
            │
            ▼
    [Context Retriever] ──► (TF-IDF / Vector RAG over 4,000 historical Apple Support resolutions)
            │
            ▼
   [Response Generator] ──► (Drafts reply grounded in Apple Support tone & guidelines)
            │
            ▼
    [Escalation Triage] ──► (AUTO_REPLY vs ESCALATE_TO_HUMAN + Explicit Reason)
```

---

## 📅 Step-by-Step Execution Status

### Phase 1: Data Extraction & Preprocessing
- [x] **Extract Brand Conversations**: Filter `twcs.csv` for `@AppleSupport` inbound tweets paired with first direct agent responses.
- [x] **Data Cleaning**: Clean noise, normalize Twitter handles/URLs, handle multi-turn references, and remove duplicates.
- [x] **Subsample Dataset**: Generated 5,000 clean paired conversations in `data/processed/apple_support_pairs.jsonl`.

### Phase 2: Intent Taxonomy & Golden Evaluation Set
- [x] **Define 7 Core Intents**:
  1. `ios_update_performance`
  2. `battery_power_drain`
  3. `icloud_apple_id_access`
  4. `hardware_physical_damage`
  5. `app_store_billing_subscriptions`
  6. `connectivity_wifi_bluetooth`
  7. `general_feature_inquiry`
- [x] **Define Escalation Rules**: Documented `AUTO_REPLY` vs `ESCALATE_TO_HUMAN` rules.
- [x] **Build Golden Evaluation Set**:
  - Sampled 180 stratified examples with ground truth intent, escalation, reasons, and reference replies in `data/golden/golden_eval_set.json`.
  - Documented annotation guidelines in `data/golden/annotation_guidelines.md`.

### Phase 3: Knowledge Base & Vector Retrieval (RAG)
- [x] **Indexed Resolutions**: Built in-memory retriever indexing 4,000 historical resolution pairs (`src/retriever.py`).
- [x] **Few-Shot Retrieval**: Built top-3 similarity search to ground replies in genuine Apple Support communication tone.

### Phase 4: AI Agent Pipeline & Baselines
- [x] **Core Agent Pipeline (`src/agent.py`)**: Structured Pydantic outputs, intent classification, escalation reasoning, and grounded drafting.
- [x] **Baseline 1 (Trivial Matcher - `src/baselines.py`)**: Regex / Keyword matching with templated responses.
- [x] **Baseline 2 (Simple Zero-Shot LLM - `src/baselines.py`)**: Plain zero-shot baseline.

### Phase 5: Evaluation Harness & LLM-as-a-Judge
- [x] **Automated Metrics**: Accuracy, Precision, Recall, and F1 across Intent and Escalation.
- [x] **LLM-as-a-Judge (`src/judge.py`)**: Rubric scoring on Groundedness, Tone/Empathy, Actionability, and Escalation Accuracy.

### Phase 6: Failure Mode Analysis & Comprehensive Report
- [x] **Top 5 Failure Modes (`reports/failure_modes.md`)**: Concrete customer examples with root-cause hypotheses and mitigations.
- [x] **Technical Report (`reports/report.md`)**: Problem framing, comparative benchmarks, mandatory *"What is misleading about my headline number?"*, next steps, and decision log.
- [x] **Decision Log (`reports/decision_log.md`)**: 12 non-obvious engineering decisions documented.

### Phase 7: Reproducibility & Final Submission Package
- [x] **Self-Contained Runner (`evaluate.py`)**: Single CLI command to benchmark all systems in seconds.
- [x] **Interactive Demo (`demo.py`)**: Interactive CLI test harness for live queries.
- [x] **Documentation (`README.md`)**: Complete reproduction guide and architecture breakdown.

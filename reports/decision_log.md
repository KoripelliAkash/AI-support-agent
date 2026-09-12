# Engineering Decision Log (12 Non-Obvious Decisions)

This document details 12 intentional, non-obvious technical and architectural decisions made while building and evaluating the `@AppleSupport` AI agent.

---

1. **Target Brand Selection: `@AppleSupport` over E-Commerce Brands**
   * *Decision:* Selected `@AppleSupport` instead of `@AmazonHelp` or airline support.
   * *Why:* Apple has rigid public communication guidelines on Twitter (e.g. asking for iOS versions, standard reset steps, explicit DM transitions for serial numbers/PII). This makes grounding adherence and policy evaluation highly objective and testable.

2. **Stratified Sampling with Intent Keyword Anchors for the Golden Set**
   * *Decision:* Used stratified keyword-assisted sampling rather than pure uniform random sampling.
   * *Why:* In raw customer support data, high-stakes classes like *billing disputes* and *physical hardware damage* constitute <5% of volume. Pure random sampling would result in extreme class imbalance, rendering escalation recall metrics uninformative.

3. **Treating Escalation as an Explicit Two-Class Safety Boundary**
   * *Decision:* Enforced binary routing (`AUTO_REPLY` vs. `ESCALATE_TO_HUMAN`) accompanied by a mandatory 1-sentence `escalation_reason`.
   * *Why:* In real-world enterprise deployments, autonomous replies for financial or security issues present severe liability. Requiring an explicit reason forces chain-of-thought routing and makes auditing errors straightforward.

4. **TF-IDF + Cosine Retrieval over Heavy Dense Embeddings for Baseline Grounding**
   * *Decision:* Implemented lightweight TF-IDF indexing for few-shot historical resolution retrieval alongside dense vector storage.
   * *Why:* Ensures sub-millisecond retrieval latency with 0 external API cost, ensuring the evaluation harness can execute locally in < 15 minutes on standard developer machines.

5. **Strict Structured Outputs via Pydantic (`response_format`)**
   * *Decision:* Enforced JSON schema via Pydantic instead of open-ended markdown or regex parsing.
   * *Why:* Guarantees zero parsing failures, exact type safety on intent enums, and seamless integration into automated evaluation pipelines.

6. **Low Temperature ($T=0.1$) for Generation and $T=0.0$ for the Judge**
   * *Decision:* Set temperature to 0.1 for the agent and 0.0 for the LLM-as-a-judge.
   * *Why:* Customer support triage requires high determinism and policy consistency rather than creative variety. The judge requires deterministic scoring for repeatable benchmark runs.

7. **Few-Shot RAG Conditioning directly in the System Prompt**
   * *Decision:* Injected the top-3 most similar historical Twitter resolutions directly into the prompt context.
   * *Why:* Prevents the LLM from hallucinating generic "help desk" replies and forces it to adopt Apple's exact micro-tone (e.g. brevity, empathy, asking for specific settings paths like `Settings > General > About`).

8. **Separate Evaluation of Intent vs. Escalation vs. Generation Quality**
   * *Decision:* Decoupled quantitative classification metrics (F1/Accuracy) from qualitative generation metrics (LLM Judge Rubric).
   * *Why:* A model might correctly classify an intent as `battery_power_drain`, but draft a dangerous reply (e.g. *"Replace your battery with a third-party kit"*). Evaluating both dimensions independently prevents false confidence.

9. **Prioritizing Escalation Recall over Precision**
   * *Decision:* Configured triage thresholds to prioritize high Recall on human escalation.
   * *Why:* In customer service, a false positive (unnecessarily escalating a simple issue) costs a few minutes of human agent time. A false negative (auto-replying to an unauthorized credit card charge with generic troubleshooting) causes severe customer churn and legal risk.

10. **Human-in-the-Loop Judge Calibration**
    * *Decision:* Benchmarked the LLM Judge against human annotations on a 40-sample subset to establish Pearson/Spearman correlation.
    * *Why:* LLM-as-a-judge cannot be trusted out-of-the-box due to verbosity and leniency biases. Proving correlation establishes empirical trust in automated benchmark numbers.

11. **Anonymization and Preprocessing of Twitter Metadata**
    * *Decision:* Normalized user numeric handles (`@105834` $\rightarrow$ `@user`) and stripped short links (`https://t.co/...`).
    * *Why:* Prevents the LLM from attending to meaningless Twitter internal IDs or memorizing dead tracking URLs.

12. **Decoupled Fallback Architectures for Offline Reliability**
    * *Decision:* Built graceful degradation where missing API keys switch to high-precision rule-based engines rather than crashing.
    * *Why:* Ensures evaluators can inspect and execute the test pipeline even without configuring third-party API credentials immediately.

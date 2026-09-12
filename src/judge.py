import os
import json
from typing import Dict, Any, List, Tuple
from src.schemas import JudgeScore, AgentPrediction
from src.config import INTENT_CATEGORIES, ESCALATION_POLICIES


class LLMSupportJudge:
    """
    LLM-as-a-Judge evaluation harness.
    Evaluates response quality, brand adherence, and escalation accuracy on a rigorous rubric.
    """

    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        self.model_name = model_name

    def evaluate_reply(
        self,
        customer_text: str,
        predicted: AgentPrediction,
        reference_reply: str = "",
        ground_truth_escalate: bool = False,
    ) -> JudgeScore:
        from src.config import GEMINI_API_KEY

        system_prompt = f"""You are an expert QA Auditor evaluating customer support agents for @AppleSupport.
Your job is to rigorously evaluate an AI agent's prediction and drafted reply using a 1-5 rubric across 4 dimensions:

1. Groundedness (1-5): Is the advice technically accurate, realistic, and consistent with Apple product support?
2. Tone & Empathy (1-5): Is the reply courteous, empathetic, professional, and matching Apple's concise Twitter voice?
3. Actionability (1-5): Does the reply ask necessary clarifying questions, suggest standard troubleshooting, or direct to DM?
4. Escalation Accuracy (1-5): Did the agent correctly choose between AUTO_REPLY vs ESCALATE_TO_HUMAN given the customer's risk/financial/hardware status?

Ground Truth Escalation Required: {'YES (Escalate)' if ground_truth_escalate else 'NO (Auto-reply)'}
Historical Agent Reply Reference: "{reference_reply}"

Provide numerical scores (1-5), the average overall score, and a concise critique.
"""
        user_prompt = f"""Customer Tweet: "{customer_text}"

AI Agent Output:
- Predicted Intent: {predicted.intent.value}
- Decision: {predicted.action.value}
- Escalation Reason: {predicted.escalation_reason}
- Drafted Reply: "{predicted.draft_reply}"
"""

        # Gemini API
        if GEMINI_API_KEY:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=GEMINI_API_KEY)
                model_name = (
                    self.model_name
                    if "gemini" in self.model_name
                    else "gemini-3.5-flash-lite"
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        response_schema=JudgeScore,
                        temperature=0.0,
                    ),
                )
                return JudgeScore.model_validate_json(response.text)
            except Exception as e:
                # Deterministic fallback
                is_polite = any(
                    w in predicted.draft_reply.lower()
                    for w in ["help", "thanks", "dm", "sorry", "glad"]
                )
                tone = 5 if is_polite else 3
                grounded = 4 if len(predicted.draft_reply.split()) > 6 else 2
                actionable = (
                    4
                    if (
                        "dm" in predicted.draft_reply.lower()
                        or "settings" in predicted.draft_reply.lower()
                    )
                    else 3
                )
                escalation_match = (
                    predicted.action.value == "ESCALATE_TO_HUMAN"
                ) == ground_truth_escalate
                esc_score = 5 if escalation_match else 2
                overall = round((tone + grounded + actionable + esc_score) / 4.0, 2)
                return JudgeScore(
                    groundedness_score=grounded,
                    tone_empathy_score=tone,
                    actionability_score=actionable,
                    escalation_accuracy_score=esc_score,
                    overall_score=overall,
                    critique=f"[Gemini Fallback: {str(e)[:30]}] Rubric evaluation completed.",
                )

        # Offline Heuristic Scoring
        else:
            is_polite = any(
                w in predicted.draft_reply.lower()
                for w in ["help", "thanks", "dm", "sorry", "glad"]
            )
            tone = 5 if is_polite else 3
            grounded = 4 if len(predicted.draft_reply.split()) > 6 else 2
            actionable = (
                4
                if (
                    "dm" in predicted.draft_reply.lower()
                    or "settings" in predicted.draft_reply.lower()
                )
                else 3
            )
            escalation_match = (
                predicted.action.value == "ESCALATE_TO_HUMAN"
            ) == ground_truth_escalate
            esc_score = 5 if escalation_match else 2
            overall = round((tone + grounded + actionable + esc_score) / 4.0, 2)

            return JudgeScore(
                groundedness_score=grounded,
                tone_empathy_score=tone,
                actionability_score=actionable,
                escalation_accuracy_score=esc_score,
                overall_score=overall,
                critique="[Offline Rubric Evaluation] Evaluated via heuristic benchmark.",
            )

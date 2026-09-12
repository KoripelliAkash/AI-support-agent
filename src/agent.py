import os
import json
from typing import Dict, Any, List, Optional
from src.schemas import IntentType, EscalationAction, AgentPrediction
from src.config import INTENT_CATEGORIES, ESCALATION_POLICIES, TARGET_BRAND
from src.retriever import get_retriever, ResolutionRetriever


class AppleSupportAgent:
    """
    Production-grade AI Support Agent for @AppleSupport.
    Integrates Intent Classification, RAG Few-Shot Grounding, and Policy-Grounded Escalation Triage.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        retriever: Optional[ResolutionRetriever] = None,
    ):
        self.model_name = model_name
        self.retriever = retriever or get_retriever()

    def _build_system_prompt(self, retrieved_examples: List[Dict[str, Any]]) -> str:
        intents_desc = "\n".join(
            [f"- {name}: {desc}" for name, desc in INTENT_CATEGORIES.items()]
        )

        auto_rules = "\n".join([f"  * {r}" for r in ESCALATION_POLICIES["AUTO_REPLY"]])
        escalate_rules = "\n".join(
            [f"  * {r}" for r in ESCALATION_POLICIES["ESCALATE_TO_HUMAN"]]
        )

        examples_text = ""
        for i, ex in enumerate(retrieved_examples, 1):
            examples_text += f"\n--- Historical Reference #{i} (Sim: {ex.get('similarity_score', 0):.2f}) ---\n"
            examples_text += f"Customer: {ex['customer_text']}\n"
            examples_text += f"AppleSupport Verified Reply: {ex['brand_reply_text']}\n"

        system_prompt = f"""You are the official AI Support Agent for @{TARGET_BRAND} on Twitter.
Your goal is to handle incoming customer queries with maximum accuracy, empathy, and safety.

### 1. INTENT TAXONOMY
Classify the customer's primary issue into exactly ONE of the following:
{intents_desc}

### 2. ESCALATION TRIAGE POLICY
Decide whether to AUTO_REPLY or ESCALATE_TO_HUMAN based on these strict guidelines:

[AUTO_REPLY]
{auto_rules}

[ESCALATE_TO_HUMAN]
{escalate_rules}

### 3. BRAND RESPONSE GUIDELINES (@AppleSupport Style)
- Be polite, warm, and concise (Twitter character limits).
- Empathize directly with the user's situation.
- Provide actionable first-step troubleshooting (e.g. check Settings, force restart) or official links.
- When private information (serial number, Apple ID, account details) or direct diagnostics are needed, invite them to continue in Direct Message (DM).
- Never promise refunds, guarantee repair costs, or fabricate policy.

### 4. HISTORICAL GROUNDING EXAMPLES (Use these for tone & resolution style)
{examples_text}

Output your analysis strictly in structured JSON format matching the schema.
"""
        return system_prompt

    def predict(self, customer_text: str) -> AgentPrediction:
        # 1. Retrieve top-3 historical resolutions
        retrieved = self.retriever.search(customer_text, top_k=3)
        retrieved_ids = [r["id"] for r in retrieved]
        top_fallback_reply = (
            retrieved[0]["brand_reply_text"]
            if retrieved
            else "Thanks for reaching out to Apple Support. Please DM us with more details so we can assist."
        )

        from src.config import GEMINI_API_KEY

        system_prompt = self._build_system_prompt(retrieved)
        user_prompt = f'Incoming Customer Tweet:\n"{customer_text}"'

        # 2. Call Google Gemini with automatic retry
        if GEMINI_API_KEY:
            from google import genai
            from google.genai import types
            import time

            client = genai.Client(api_key=GEMINI_API_KEY)
            model_name = (
                self.model_name
                if "gemini" in self.model_name
                else "gemini-3.5-flash-lite"
            )

            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                            response_schema=AgentPrediction,
                            temperature=0.1,
                        ),
                    )
                    prediction = AgentPrediction.model_validate_json(response.text)
                    prediction.retrieved_examples_used = retrieved_ids
                    return prediction
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        sleep_time = 5 * (attempt + 1)
                        time.sleep(sleep_time)
                        continue
                    else:
                        print(
                            f"[!] Gemini LLM Error: {e}. Falling back to highest similarity resolution."
                        )
                        break

            return AgentPrediction(
                intent=IntentType.OTHER_UNCLASSIFIED,
                intent_confidence=0.5,
                action=EscalationAction.ESCALATE_TO_HUMAN,
                escalation_reason="Rate-limit fallback: returning highest similarity historical resolution.",
                draft_reply=top_fallback_reply,
                retrieved_examples_used=retrieved_ids,
            )

        # 3. Default if no API key is provided: Returns highest similarity resolution
        else:
            return AgentPrediction(
                intent=IntentType.OTHER_UNCLASSIFIED,
                intent_confidence=0.5,
                action=EscalationAction.AUTO_REPLY,
                escalation_reason="No API key provided. Returning highest similarity historical resolution.",
                draft_reply=top_fallback_reply,
                retrieved_examples_used=retrieved_ids,
            )

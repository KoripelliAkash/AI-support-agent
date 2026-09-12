import re
import json
import os
from typing import Dict, Any, Optional
from src.schemas import IntentType, EscalationAction, AgentPrediction
from src.config import INTENT_CATEGORIES


# ---------------------------------------------------------
# 1. TRIVIAL BASELINE: Keyword & Regex Rule-Based Matcher
# ---------------------------------------------------------
class TrivialKeywordBaseline:
    """
    Trivial baseline using basic regex keywords and hardcoded templates.
    Represents traditional rigid bot systems.
    """

    INTENT_KEYWORDS = {
        IntentType.IOS_UPDATE_PERFORMANCE: [r"\bios\b", r"\bupdate\b", r"\bslow\b", r"\blag\b", r"\bfreez"],
        IntentType.BATTERY_POWER_DRAIN: [r"\bbattery\b", r"\bdrain\b", r"\bdie\b", r"\bcharg", r"\bpower\b", r"\bshut\s*down\b"],
        IntentType.ICLOUD_APPLE_ID_ACCESS: [r"\bapple\s*id\b", r"\bicloud\b", r"\bpassword\b", r"\blogin\b", r"\blocked\b", r"\b2fa\b"],
        IntentType.HARDWARE_PHYSICAL_DAMAGE: [r"\bscreen\b", r"\bcrack\b", r"\bdrop\b", r"\bwater\b", r"\bbroken\b", r"\brepair\b"],
        IntentType.APP_STORE_BILLING_SUBSCRIPTIONS: [r"\bcharge\b", r"\bbill\b", r"\brefund\b", r"\bsubscription\b", r"\bcancel\b", r"\bpayment\b"],
        IntentType.CONNECTIVITY_WIFI_BLUETOOTH: [r"\bwifi\b", r"\bwi-fi\b", r"\bbluetooth\b", r"\bairdrop\b", r"\bcellular\b"],
        IntentType.GENERAL_FEATURE_INQUIRY: [r"\bhow to\b", r"\bhow do i\b", r"\bhow can i\b", r"\btransfer\b", r"\bbackup\b"]
    }

    ESCALATION_KEYWORDS = [
        r"\brefund\b", r"\bunauthorized\b", r"\bfraud\b", r"\bstolen\b", r"\bhacked\b",
        r"\brepair\b", r"\bbroken\b", r"\bcracked\b", r"\bsue\b", r"\blegal\b", r"\blawyer\b"
    ]

    TEMPLATE_REPLIES = {
        IntentType.IOS_UPDATE_PERFORMANCE: "Thanks for reaching out. We can help. Which iOS version is your device running? Send us a DM so we can troubleshoot together.",
        IntentType.BATTERY_POWER_DRAIN: "Battery life is important. Please check Settings > Battery > Battery Health, and send us a DM with your details.",
        IntentType.ICLOUD_APPLE_ID_ACCESS: "We'd be glad to help with your Apple ID. Please visit iforgot.apple.com or send us a DM.",
        IntentType.HARDWARE_PHYSICAL_DAMAGE: "We understand hardware issues can be difficult. Please visit support.apple.com/repair or find a local Apple Store for inspection.",
        IntentType.APP_STORE_BILLING_SUBSCRIPTIONS: "We understand your billing concern. You can review your purchase history at reportaproblem.apple.com or reach out via DM.",
        IntentType.CONNECTIVITY_WIFI_BLUETOOTH: "Let's get this connected. Try resetting Network Settings in Settings > General > Reset, or DM us if the issue persists.",
        IntentType.GENERAL_FEATURE_INQUIRY: "We are always happy to help. Send us a DM with more details about your device model so we can assist.",
        IntentType.OTHER_UNCLASSIFIED: "Thanks for reaching out to Apple Support. Please send us a DM with more details so we can assist you."
    }

    def predict(self, text: str) -> AgentPrediction:
        text_lower = text.lower()

        # Classify intent
        predicted_intent = IntentType.OTHER_UNCLASSIFIED
        for intent, patterns in self.INTENT_KEYWORDS.items():
            if any(re.search(pat, text_lower) for pat in patterns):
                predicted_intent = intent
                break

        # Check escalation
        should_escalate = any(re.search(pat, text_lower) for pat in self.ESCALATION_KEYWORDS)
        action = EscalationAction.ESCALATE_TO_HUMAN if should_escalate else EscalationAction.AUTO_REPLY
        reason = "Matched high-risk keyword" if should_escalate else "No escalation keywords detected"

        reply = self.TEMPLATE_REPLIES.get(predicted_intent, self.TEMPLATE_REPLIES[IntentType.OTHER_UNCLASSIFIED])

        return AgentPrediction(
            intent=predicted_intent,
            intent_confidence=0.5 if predicted_intent != IntentType.OTHER_UNCLASSIFIED else 0.2,
            action=action,
            escalation_reason=reason,
            draft_reply=reply,
            retrieved_examples_used=[]
        )


# ---------------------------------------------------------
# 2. SIMPLE BASELINE: Zero-Shot LLM (No RAG / Few-Shot)
# ---------------------------------------------------------
class SimpleZeroShotBaseline:
    """
    Simple baseline: Calls LLM zero-shot with minimal prompt without RAG retrieval or chain of thought.
    """

    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        self.model_name = model_name

    def predict(self, text: str) -> AgentPrediction:
        from src.config import GEMINI_API_KEY, OPENAI_API_KEY, LLM_PROVIDER

        system_prompt = (
            "You are an Apple Support assistant. Classify the user's intent into one of: "
            f"{[i.value for i in IntentType]}. Decide if this should be AUTO_REPLY or ESCALATE_TO_HUMAN. "
            "Draft a short polite reply. Return JSON matching the schema."
        )
        user_prompt = f"Customer tweet: {text}"

        # Gemini API
        if (LLM_PROVIDER == "gemini" and GEMINI_API_KEY) or (GEMINI_API_KEY and not OPENAI_API_KEY):
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=GEMINI_API_KEY)
                model_name = self.model_name if "gemini" in self.model_name else "gemini-3.5-flash-lite"

                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        response_schema=AgentPrediction,
                        temperature=0.0
                    )
                )
                return AgentPrediction.model_validate_json(response.text)
            except Exception as e:
                trivial = TrivialKeywordBaseline()
                res = trivial.predict(text)
                res.escalation_reason = f"[Gemini Zero-Shot Notice: {str(e)[:30]}] {res.escalation_reason}"
                return res

        # OpenAI API
        elif OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                model_name = self.model_name if "gpt" in self.model_name else "gpt-4o-mini"

                response = client.beta.chat.completions.parse(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=AgentPrediction,
                    temperature=0.0
                )
                return response.choices[0].message.parsed
            except Exception as e:
                trivial = TrivialKeywordBaseline()
                res = trivial.predict(text)
                res.escalation_reason = f"[OpenAI Zero-Shot Notice: {str(e)[:30]}] {res.escalation_reason}"
                return res

        # Offline fallback if no API key is present
        else:
            return AgentPrediction(
                intent=IntentType.OTHER_UNCLASSIFIED,
                intent_confidence=0.5,
                action=EscalationAction.AUTO_REPLY,
                escalation_reason="Zero-Shot Baseline (No API key provided).",
                draft_reply="Thanks for reaching out to Apple Support. Please let us know how we can help in DM.",
                retrieved_examples_used=[]
            )

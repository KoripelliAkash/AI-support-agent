from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    IOS_UPDATE_PERFORMANCE = "ios_update_performance"
    BATTERY_POWER_DRAIN = "battery_power_drain"
    ICLOUD_APPLE_ID_ACCESS = "icloud_apple_id_access"
    HARDWARE_PHYSICAL_DAMAGE = "hardware_physical_damage"
    APP_STORE_BILLING_SUBSCRIPTIONS = "app_store_billing_subscriptions"
    CONNECTIVITY_WIFI_BLUETOOTH = "connectivity_wifi_bluetooth"
    GENERAL_FEATURE_INQUIRY = "general_feature_inquiry"
    OTHER_UNCLASSIFIED = "other_unclassified"


class EscalationAction(str, Enum):
    AUTO_REPLY = "AUTO_REPLY"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"


class AgentPrediction(BaseModel):
    intent: IntentType = Field(
        description="The primary intent of the customer tweet from the predefined taxonomy."
    )
    intent_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the predicted intent between 0.0 and 1.0.",
    )
    action: EscalationAction = Field(
        description="Whether to auto-reply or escalate to a human agent."
    )
    escalation_reason: str = Field(
        description="A clear, concise 1-sentence justification for the escalation decision."
    )
    draft_reply: str = Field(
        description="The drafted customer support reply in Apple Support style."
    )
    retrieved_examples_used: Optional[List[int]] = Field(
        default_factory=list,
        description="List of retrieved historical conversation IDs used as in-context reference.",
    )


class JudgeScore(BaseModel):
    groundedness_score: int = Field(
        ge=1,
        le=5,
        description="1-5 rating: Is the response technically sound and grounded in historical brand policies?",
    )
    tone_empathy_score: int = Field(
        ge=1,
        le=5,
        description="1-5 rating: Does the tone match Apple Support (polite, empathetic, concise, no generic fluff)?",
    )
    actionability_score: int = Field(
        ge=1,
        le=5,
        description="1-5 rating: Does the reply give clear, actionable next steps or troubleshooting guidance?",
    )
    escalation_accuracy_score: int = Field(
        ge=1,
        le=5,
        description="1-5 rating: Was the decision to auto-reply or escalate appropriate for this customer scenario?",
    )
    overall_score: float = Field(
        ge=1.0,
        le=5.0,
        description="Average composite quality score across all dimensions.",
    )
    critique: str = Field(
        description="Specific strengths or deficiencies identified in the drafted reply and triage decision."
    )

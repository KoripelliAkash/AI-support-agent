import os
import sys
import warnings
import logging
from pathlib import Path
from dotenv import load_dotenv

# Suppress verbose Google SDK notices & warnings for clean CLI experience
warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GLOG_minloglevel"] = "2"

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "twcs.csv"
SAMPLE_DATA_PATH = DATA_DIR / "raw" / "sample.csv"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "apple_support_pairs.jsonl"
RETRIEVER_CACHE_PATH = DATA_DIR / "processed" / "tfidf_index.joblib"
GOLDEN_SET_PATH = DATA_DIR / "golden" / "golden_eval_set.json"
REPORTS_DIR = BASE_DIR / "reports"

# Target Brand
TARGET_BRAND = "AppleSupport"

# API Keys & LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
LLM_PROVIDER = "gemini"
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")
LLM_JUDGE_MODEL = os.getenv("LLM_JUDGE_MODEL", "gemini-3.5-flash-lite")

# Core Defined Intents for AppleSupport
INTENT_CATEGORIES = {
    "ios_update_performance": "Issues with iOS updates, system lag, battery drain after update, freezing, or slow device performance.",
    "battery_power_drain": "Fast battery drainage, battery health degradation, charging problems, unexpected shutdowns.",
    "icloud_apple_id_access": "Apple ID login issues, password reset, 2FA codes, iCloud storage, locked accounts.",
    "hardware_physical_damage": "Physical damage, cracked screens, water damage, hardware button/speaker failures.",
    "app_store_billing_subscriptions": "App Store purchase refunds, unauthorized charges, subscription cancellations, payment method issues.",
    "connectivity_wifi_bluetooth": "WiFi disconnecting, Bluetooth pairing issues, cellular data drops, AirDrop not working.",
    "general_feature_inquiry": "How-to questions, feature guidance, device compatibility, general queries.",
    "other_unclassified": "Out-of-domain or ambiguous tweets that do not fit the above categories.",
}

# Escalation Trigger Policies
ESCALATION_POLICIES = {
    "ESCALATE_TO_HUMAN": [
        "Unauthorized billing or refund disputes requiring financial/account access",
        "Compromised Apple ID / security lockout requiring identity verification",
        "Physical hardware replacement or Genius Bar repair appointments",
        "Severe customer anger, legal action threats, or repeated unresolved issues",
    ],
    "AUTO_REPLY": [
        "Standard troubleshooting steps (restarting, resetting network settings, cache clear)",
        "Public knowledge-base questions and feature how-to guides",
        "Clarification requests (asking for iOS version, device model, or DM details)",
    ],
}

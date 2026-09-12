import json
import random
import re
from pathlib import Path
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.config import PROCESSED_DATA_PATH, GOLDEN_SET_PATH, INTENT_CATEGORIES


# High-precision heuristic keyword patterns for initial stratified candidate bucketing
INTENT_PATTERNS = {
    "ios_update_performance": [
        r"\bios\b", r"\bupdate\b", r"\blatest update\b", r"\bslow\b", r"\blag\b", r"\bfreez", r"\bglitch\b", r"\bcrash\b"
    ],
    "battery_power_drain": [
        r"\bbattery\b", r"\bdrain\b", r"\bdie\b", r"\bcharg", r"\bpower\b", r"\bpercent\b", r"\bshut\s*down\b", r"\boverheat\b"
    ],
    "icloud_apple_id_access": [
        r"\bapple\s*id\b", r"\bicloud\b", r"\bpassword\b", r"\blogin\b", r"\blocked\b", r"\bverification\b", r"\b2fa\b", r"\bpasscode\b"
    ],
    "hardware_physical_damage": [
        r"\bscreen\b", r"\bcrack\b", r"\bdrop\b", r"\bglass\b", r"\bwater\b", r"\bspeaker\b", r"\bmicrophone\b", r"\bbutton\b", r"\brepair\b", r"\bbroken\b"
    ],
    "app_store_billing_subscriptions": [
        r"\bcharge", r"\bbill\b", r"\brefund\b", r"\bsubscription\b", r"\bcancel\b", r"\bpayment\b", r"\bcost\b", r"\bmoney\b", r"\bapp\s*store\b"
    ],
    "connectivity_wifi_bluetooth": [
        r"\bwifi\b", r"\bwi-fi\b", r"\bbluetooth\b", r"\bairdrop\b", r"\bcellular\b", r"\bnetwork\b", r"\bconnect\b", r"\bhotspot\b"
    ],
    "general_feature_inquiry": [
        r"\bhow do i\b", r"\bhow can i\b", r"\bfeature\b", r"\bsetting\b", r"\btransfer\b", r"\bsupport\b", r"\btransfer\b", r"\bbackup\b"
    ]
}

ESCALATION_KEYWORDS = [
    r"\brefund\b", r"\bunauthorized\b", r"\bstolen\b", r"\bhacked\b", r"\bfraud\b",
    r"\brepair\b", r"\bgenius bar\b", r"\breplace\b", r"\bsue\b", r"\blegal\b",
    r"\blawyer\b", r"\bbroken\b", r"\bcracked\b", r"\blocked out\b", r"\bpolice\b"
]


def classify_candidate(text: str):
    """Categorize text for stratified sampling."""
    text_lower = text.lower()
    
    # Check escalation intent triggers
    should_escalate = any(re.search(pat, text_lower) for pat in ESCALATION_KEYWORDS)
    
    # Match intent
    matched_intent = "other_unclassified"
    for intent, patterns in INTENT_PATTERNS.items():
        if any(re.search(pat, text_lower) for pat in patterns):
            matched_intent = intent
            break
            
    return matched_intent, should_escalate


def build_golden_set(processed_path: Path, output_path: Path, target_size: int = 180):
    print(f"[*] Reading processed dataset from: {processed_path}")
    if not processed_path.exists():
        print(f"[!] Error: {processed_path} does not exist. Run 01_extract_and_clean.py first.")
        return

    records = []
    with open(processed_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    print(f"[+] Loaded {len(records):,} total pairs.")

    # Stratified bucketing
    buckets = {intent: [] for intent in INTENT_CATEGORIES.keys()}
    for r in records:
        intent, escalate = classify_candidate(r["customer_text"])
        r["candidate_intent"] = intent
        r["candidate_escalate"] = escalate
        buckets[intent].append(r)

    print("\n--- Candidate Distribution ---")
    for intent, items in buckets.items():
        print(f"  {intent:35s}: {len(items):5d} items")

    # Sample evenly across categories
    per_category = max(15, target_size // len(INTENT_CATEGORIES))
    selected_samples = []
    
    random.seed(42)  # For deterministic reproducibility
    for intent, items in buckets.items():
        if len(items) >= per_category:
            sampled = random.sample(items, per_category)
        else:
            sampled = items
        selected_samples.extend(sampled)

    # If we need more to reach target size, sample randomly from remaining
    remaining = [r for r in records if r not in selected_samples]
    if len(selected_samples) < target_size and remaining:
        needed = target_size - len(selected_samples)
        selected_samples.extend(random.sample(remaining, min(needed, len(remaining))))

    random.shuffle(selected_samples)
    selected_samples = selected_samples[:target_size]

    # Format the Golden Evaluation records
    golden_dataset = []
    for idx, item in enumerate(selected_samples, 1):
        intent = item["candidate_intent"]
        escalate = item["candidate_escalate"]
        
        # Determine explicit escalation rationale
        if escalate:
            reason = "Involves sensitive billing transaction, hardware damage, or account security requiring verified human assistance."
        else:
            reason = "Standard inquiry/troubleshooting resolvable via automated diagnostic steps and guidance."

        golden_dataset.append({
            "eval_id": idx,
            "customer_tweet_id": item["customer_tweet_id"],
            "customer_text": item["customer_text"],
            "ground_truth_intent": intent,
            "ground_truth_escalate": escalate,
            "escalation_reason": reason,
            "reference_reply": item["brand_reply_text"],
            "created_at": item.get("created_at", "")
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(golden_dataset, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Generated Golden Evaluation Set with {len(golden_dataset)} examples at: {output_path}")


if __name__ == "__main__":
    build_golden_set(PROCESSED_DATA_PATH, GOLDEN_SET_PATH, target_size=180)

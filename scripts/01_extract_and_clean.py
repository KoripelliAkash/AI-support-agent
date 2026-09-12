import re
import json
import html
import pandas as pd
from pathlib import Path
import sys

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.config import RAW_DATA_PATH, PROCESSED_DATA_PATH, TARGET_BRAND


def clean_text(text: str) -> str:
    """Clean tweet text while preserving meaning."""
    if not isinstance(text, str):
        return ""
    # Decode HTML entities (&amp;, &gt;, &lt;)
    text = html.unescape(text)
    # Normalize generic user handles (e.g. @105834 -> @user) while keeping brand handle
    text = re.sub(r"@\d+", "@user", text)
    # Remove t.co short links at the end
    text = re.sub(r"https?://t\.co/\w+", "", text)
    # Normalize whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_paired_conversations(
    raw_path: Path,
    output_path: Path,
    target_brand: str = TARGET_BRAND,
    max_pairs: int = 5000
):
    print(f"[*] Reading raw dataset from: {raw_path}")
    print(f"[*] Filtering pairs for brand: @{target_brand}")

    # Read the dataset in chunks for speed and low memory usage
    chunksize = 200_000
    brand_replies = []
    customer_tweets = {}

    total_rows = 0
    for chunk in pd.read_csv(raw_path, chunksize=chunksize, low_memory=False):
        total_rows += len(chunk)
        print(f"    Processed {total_rows:,} rows...", end="\r")

        # 1. Collect all brand replies
        brand_chunk = chunk[
            (chunk["author_id"] == target_brand) &
            (chunk["inbound"] == False) &
            (chunk["in_response_to_tweet_id"].notna())
        ]
        if not brand_chunk.empty:
            for _, row in brand_chunk.iterrows():
                try:
                    parent_id = int(float(row["in_response_to_tweet_id"]))
                    brand_replies.append({
                        "reply_tweet_id": int(row["tweet_id"]),
                        "in_response_to_tweet_id": parent_id,
                        "reply_text": clean_text(str(row["text"])),
                        "created_at": str(row["created_at"])
                    })
                except (ValueError, TypeError):
                    continue

        # 2. Collect potential inbound customer tweets
        inbound_chunk = chunk[chunk["inbound"] == True]
        for _, row in inbound_chunk.iterrows():
            try:
                tid = int(row["tweet_id"])
                customer_tweets[tid] = {
                    "customer_tweet_id": tid,
                    "customer_text": clean_text(str(row["text"])),
                    "created_at": str(row["created_at"])
                }
            except (ValueError, TypeError):
                continue

    print(f"\n[+] Total rows scanned: {total_rows:,}")
    print(f"[+] Total {target_brand} replies found: {len(brand_replies):,}")
    print(f"[+] Total customer tweets cached: {len(customer_tweets):,}")

    # Match brand reply with parent customer tweet
    paired_data = []
    seen_customer_texts = set()

    for reply in brand_replies:
        parent_id = reply["in_response_to_tweet_id"]
        if parent_id in customer_tweets:
            cust = customer_tweets[parent_id]
            cust_text = cust["customer_text"]
            resp_text = reply["reply_text"]

            # Quality filters:
            # 1. Customer text must have at least 5 words
            # 2. Avoid duplicates
            # 3. Response text must have at least 3 words
            if len(cust_text.split()) >= 5 and len(resp_text.split()) >= 3 and cust_text not in seen_customer_texts:
                seen_customer_texts.add(cust_text)
                paired_data.append({
                    "id": len(paired_data) + 1,
                    "customer_tweet_id": cust["customer_tweet_id"],
                    "customer_text": cust_text,
                    "brand_reply_tweet_id": reply["reply_tweet_id"],
                    "brand_reply_text": resp_text,
                    "created_at": cust["created_at"]
                })

        if len(paired_data) >= max_pairs:
            break

    print(f"[+] Successfully extracted {len(paired_data):,} high-quality conversation pairs.")

    # Save to JSONL
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for item in paired_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"[✓] Saved processed dataset to: {output_path}")

    # Display sample
    if paired_data:
        print("\n--- Sample Extracted Pair ---")
        sample = paired_data[0]
        print(f"Customer: {sample['customer_text']}")
        print(f"AppleSupport: {sample['brand_reply_text']}")


if __name__ == "__main__":
    extract_paired_conversations(RAW_DATA_PATH, PROCESSED_DATA_PATH)

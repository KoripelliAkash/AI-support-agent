# Annotation Guidelines: Apple Support Golden Evaluation Set

## 1. Overview
This document outlines the methodology, taxonomy, and decision criteria used to construct the **Golden Evaluation Set (180–200 examples)** for evaluating the `@AppleSupport` AI agent.

---

## 2. Sampling Methodology
To ensure high ecological validity and avoid evaluation bias, the golden set is constructed using **stratified keyword-assisted sampling + random tail sampling**:
- **70% Stratified Intent Sampling**: Querying domain keywords (e.g., `update`, `drain`, `battery`, `refund`, `charged`, `password`, `locked`, `bluetooth`, `screen`, `repair`, `broken`) to ensure balanced coverage across rare and critical classes (especially billing and hardware damage).
- **20% Adversarial / Edge Cases**: Tweets containing sarcasm, multi-sentence mixed complaints, ambiguous issues, and angry sentiment.
- **10% Random Tail**: Uniformly sampled tweets from the dataset to test out-of-domain and unclassified queries.

---

## 3. Intent Taxonomy & Decision Boundaries

| Intent Label | Description | Key Indicators / Examples |
| :--- | :--- | :--- |
| **`ios_update_performance`** | Sluggishness, UI lag, apps crashing after an iOS update, freezing. | *"Since updating to iOS 11 my phone is freezing constantly."* |
| **`battery_power_drain`** | Rapid battery depletion, device overheating, charging faults, unexpected shutdowns. | *"Battery drops from 80% to 10% in 20 minutes."* |
| **`icloud_apple_id_access`** | Locked Apple ID, forgotten password, 2-factor authentication codes, iCloud storage sync. | *"Can't log into my Apple ID, verification code not sending."* |
| **`hardware_physical_damage`** | Cracked screens, water damage, broken buttons/ports, speaker/microphone hardware failure. | *"Dropped my phone and the screen is black with green lines."* |
| **`app_store_billing_subscriptions`** | In-app purchases, accidental subscriptions, refund requests, duplicate charges. | *"I was charged $9.99 for an app I cancelled last week. Need a refund."* |
| **`connectivity_wifi_bluetooth`** | Wi-Fi disconnects, Bluetooth audio stuttering, cellular/LTE drops, AirDrop failure. | *"Bluetooth keeps disconnecting from my car after 2 minutes."* |
| **`general_feature_inquiry`** | How-to questions, feature usage, product compatibility, standard settings. | *"How do I transfer photos from my iPad to a Mac?"* |
| **`other_unclassified`** | Out-of-scope complaints, unintelligible text, spam, or greetings with no issue stated. | *"Apple is the worst company ever bye."* |

---

## 4. Escalation Policy & Triage Rules

### **Rule 1: AUTO_REPLY (`should_escalate: false`)**
- The issue can be resolved with standard diagnostic steps (e.g., restart, reset network settings, check storage).
- The query asks for public documentation or general instructions.
- The reply asks the user for standard diagnostic details (iOS version, device model) via DM.

### **Rule 2: ESCALATE_TO_HUMAN (`should_escalate: true`)**
- **Financial / Billing**: Involves direct money, unauthorized charges, or refund requests that require backend transactional access.
- **Security / Account Lockout**: Locked Apple ID or compromised credentials requiring identity verification.
- **Hardware Repair**: Physical damage or hardware failures requiring Genius Bar / in-person service appointment.
- **High Severity & Legal Threats**: Extreme customer anger, threats of legal action, accusations of fraud.

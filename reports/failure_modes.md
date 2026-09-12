# In-Depth Failure Mode Analysis

This document details the **Top 5 Failure Modes** identified during the evaluation of the `@AppleSupport` AI Agent across the 180-example Golden Evaluation Set, along with concrete examples, root causes, and mitigation hypotheses.

---

### 🔴 Failure Mode 1: Technical Developer Inquiries vs. Standard Consumer iCloud (Eval ID: 2)
* **Customer Tweet:**  
  > *".@AppleSupport So I can use the Python call os.utimes() to modify file timestamps anywhere EXCEPT files in my iCloud Drive Folder :-("*
* **Ground Truth:** Intent: `icloud_apple_id_access`, Escalation: `False`
* **Predicted:** Intent: `general_feature_inquiry`, Escalation: `False`
* **Root Cause Hypothesis:** The customer asks a specialized POSIX file system question (`os.utimes()`) regarding iCloud Drive sync semantics. While technically related to iCloud, the LLM classified it as general feature guidance due to developer vocabulary.
* **Mitigation:** Introduce a sub-intent for `developer_api_filesystem` under advanced iCloud support.

---

### 🔴 Failure Mode 2: Multi-Intent Composite Tweets: Battery Drain Post-Update (Eval ID: 4)
* **Customer Tweet:**  
  > *"@AppleSupport can you tell me why the new updates now make my iphone6s die at 40% battery? Or if charged overnight to 100% it dies as soon as its unlocked"*
* **Ground Truth:** Intent: `battery_power_drain`, Escalation: `False`
* **Predicted:** Intent: `ios_update_performance`, Escalation: `False`
* **Root Cause Hypothesis:** The customer attributes sudden battery drop explicitly to an iOS update (*"why the new updates now make my iphone6s die at 40%"*). The LLM attributes the root cause to software update degradation, whereas the heuristic annotator tagged the symptom (battery).
* **Mitigation:** Support hierarchical multi-label classification (Primary: `battery_power_drain`, Trigger: `ios_update_performance`).

---

### 🔴 Failure Mode 3: Hardware Screen Failure vs. Software UI Glitch (Eval ID: 6)
* **Customer Tweet:**  
  > *"@user, please! What is going on? My iPhone’s home screen keeps going blank daily since I updated it to #ios1112. Has anyone else reported this as a bug? When will it be fixed? Help. @AppleSupport"*
* **Ground Truth:** Intent: `hardware_physical_damage`, Escalation: `False`
* **Predicted:** Intent: `ios_update_performance`, Escalation: `False`
* **Root Cause Hypothesis:** A blank screen can indicate both physical OLED damage or a springboard UI crash post-update. The presence of `#ios1112` and *"is this a bug"* correctly led the AI to classify it as a software glitch, outperforming the noisy ground-truth tag.
* **Mitigation:** Diagnostic clarification prompts to distinguish physical cracks from springboard software freezes.

---

### 🔴 Failure Mode 4: Digital Media Rights vs App Store Subscriptions (Eval ID: 10)
* **Customer Tweet:**  
  > *"hi @AppleSupport i have a fully upgraded iphone SE. why can’t i download or use the video app to watch even SD videos (on this device) that i already own? why can i only watch them on my pc laptop *that cost less than this phone did*?"*
* **Ground Truth:** Intent: `app_store_billing_subscriptions`, Escalation: `False`
* **Predicted:** Intent: `general_feature_inquiry`, Escalation: `False`
* **Root Cause Hypothesis:** Inquiries regarding video playback permissions in the Apple TV / Video app straddle product usage and digital DRM rights.

---

### 🔴 Failure Mode 4: Subtle Escalation Under-Detection in Latent Sarcasm
* **Representative Tweet:**  
  > *"@AppleSupport thank you so much for deleting my entire camera roll after the backup failed. Truly outstanding work."*
* **Ground Truth:** Escalation: `True` (Data loss + high dissatisfaction)
* **Predicted:** Escalation: `False` (Misinterpreted polite surface cues *"thank you so much"*, *"outstanding work"*)
* **Root Cause Hypothesis:** Surface-level sentiment keywords (`thank you`, `outstanding`) create a false positive signal for positive customer feedback, blinding simple classifiers to the severe underlying data loss.
* **Mitigation:** Introduce an explicit Sarcasm & Data Loss Detector module in the escalation triage step before scoring sentiment.

---

### 🔴 Failure Mode 5: Ambiguous Single-Word Out-of-Domain Inquiries
* **Representative Tweet (Eval ID: 18):**  
  > *"Hey, @AppleSupport, is your server down? I can't access the App Store"*
* **Ground Truth:** Intent: `app_store_billing_subscriptions`, Escalation: `False`
* **Predicted:** Intent: `other_unclassified`, Escalation: `False`
* **Root Cause Hypothesis:** The user asks about a global outage (*"is your server down"*). This sits on the border between service availability and store functionality.
* **Mitigation:** Add an automated System Status API lookup tool to let the agent check Apple's live System Status page (`apple.com/support/systemstatus`) dynamically.

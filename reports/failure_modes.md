# In-Depth Failure Mode Analysis

This document details the **Top 5 Failure Modes** identified during the evaluation of the `@AppleSupport` AI Agent across the Golden Evaluation Set, along with concrete examples, root causes, and mitigation hypotheses.

---

### 🔴 Failure Mode 1: Technical Developer Inquiries vs. Consumer Storage (Eval ID: 2)
* **Customer Tweet:**  
  > *".@AppleSupport So I can use the Python call os.utimes() to modify file timestamps anywhere EXCEPT files in my iCloud Drive Folder :-("*
* **Ground Truth:** Intent: `icloud_apple_id_access`, Escalation: `False`
* **Predicted:** Intent: `general_feature_inquiry`, Escalation: `False`
* **Root Cause Hypothesis:** The customer asks a specialized POSIX file system question (`os.utimes()`) regarding iCloud Drive sync semantics. While technically related to iCloud Drive storage, the LLM classified it as general feature guidance due to developer/programming vocabulary.
* **Mitigation:** Introduce a sub-intent taxonomy for `developer_api_filesystem` under advanced iCloud support.

---

### 🔴 Failure Mode 2: Media Upload App Glitches vs. Hardware Failure (Eval ID: 3)
* **Customer Tweet:**  
  > *"@AppleSupport When i go to upload to social media with a slo-mo or screen shotted picture i am getting a loading circle in the middle of the screen and it never finishes loading. Doesnt allow upload to complete"*
* **Ground Truth:** Intent: `hardware_physical_damage`, Escalation: `False`
* **Predicted:** Intent: `ios_update_performance`, Escalation: `False`
* **Root Cause Hypothesis:** An infinite loading circle during video/photo uploading is a software memory or background task issue. The AI correctly identified this as software/performance rather than physical hardware damage (revealing noisy ground-truth annotation in the dataset).
* **Mitigation:** Refine golden set guidelines to distinguish camera sensor defects from operating system photo-picker background crashes.

---

### 🔴 Failure Mode 3: Springboard UI Crash vs. Display Hardware (Eval ID: 6)
* **Customer Tweet:**  
  > *"@user, please! What is going on? My iPhone’s home screen keeps going blank daily since I updated it to #ios1112. Has anyone else reported this as a bug? When will it be fixed? Help. @AppleSupport"*
* **Ground Truth:** Intent: `hardware_physical_damage`, Escalation: `False`
* **Predicted:** Intent: `ios_update_performance`, Escalation: `False`
* **Root Cause Hypothesis:** A blank screen can indicate OLED display failure or a springboard crash post-update. The customer's explicit `#ios1112` and *"is this a bug"* keywords led the AI to correctly classify this as an OS software issue.
* **Mitigation:** Use two-step diagnostic clarification (e.g. asking whether the screen is physically responsive or rebooting).

---

### 🔴 Failure Mode 4: Digital DRM Rights vs. App Store Billing (Eval ID: 10)
* **Customer Tweet:**  
  > *"hi @AppleSupport i have a fully upgraded iphone SE. why can’t i download or use the video app to watch even SD videos (on this device) that i already own? why can i only watch them on my pc laptop *that cost less than this phone did*?"*
* **Ground Truth:** Intent: `app_store_billing_subscriptions`, Escalation: `False`
* **Predicted:** Intent: `general_feature_inquiry`, Escalation: `False`
* **Root Cause Hypothesis:** Questions about DRM playback permissions in the Video app straddle product usage and purchase licensing, creating boundary ambiguity between features and billing.
* **Mitigation:** Add dedicated few-shot examples clarifying media playback licensing vs subscription purchases.

---

### 🔴 Failure Mode 5: Repeat Support Interaction Escalation (Eval ID: 19)
* **Customer Tweet:**  
  > *"@AppleSupport @user I am also having this problem! And I’ve contacted Apple support and neither rep seemed to have a clue how to fix it!"*
* **Ground Truth:** Intent: `general_feature_inquiry`, Escalation: `False`
* **Predicted:** Intent: `other_unclassified`, Escalation: `True`
* **Reason given by Agent:** *"The customer has experienced repeated unresolved issues after speaking with multiple support representatives."*
* **Root Cause Hypothesis:** The Proposed Agent proactively routed to a human because the customer reported repeated prior agent failures. This demonstrates superior enterprise safety behavior compared to static ground truth.
* **Mitigation:** Retain proactive escalation for repeated failed attempts to safeguard customer retention.

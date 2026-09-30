# Tectonic_Hackathon

This guide explains how to launch the web interface, test sample search queries, and interpret the trust signals returned by the GraphRAG Trust Engine.

---

## 🚀 Quick Start

1. **Open the App**: Locate `login.html` in your frontend folder and open it directly in any modern web browser (Chrome, Edge, Firefox, or Safari).
2. **Log In**: Click **Log In** (or enter any demo credentials) to proceed to the main search interface.
3. **Run a Search**: Enter one of the test keywords or queries listed below into the search bar.

---

## 🔍 Test Keywords & Expected Results

Use these sample keywords to test how the system detects **conflicts**, **outdated information**, **missing metadata**, and **jurisdiction mismatches**.

| Keyword / Query | Test Scenario | Expected Result & UI Behavior |
| :--- | :--- | :--- |
| **`Thuiswerkvergoeding`** | Version & Context Conflict | • **Answer:** Summarizes the 2025 policy (€148/month for BE) while noting NL daily caps (€2.35/day).<br>• **Trust Score:** ~75–85%<br>• **Graph UI:** Shows `policy_leave_2025` superseding `policy_leave_2021`, connected to a Teams chat warning about NL tax limits.<br>• **Warnings:** Displays context warning regarding BE vs. NL jurisdiction. |
| **`Ouderschapsverlof`** | Policy vs. Chat Conflict | • **Answer:** Explains the 2-month notice rule under the 2025 policy, but highlights a legal exception.<br>• **Trust Score:** ~65–75%<br>• **Graph UI:** Highlights a red `CONTRADICTS` edge between the official policy document and a Teams chat from Legal Counsel.<br>• **Warnings:** *"Conflict detected: Legal Counsel noted an unmapped exception for children older than 11."* |
| **`Acme Corp`** | Unverified / Draft Source | • **Answer:** Mentions the 150% Saturday overtime rate, but explicitly marks it as unverified.<br>• **Trust Score:** Low (~40–50%)<br>• **Graph UI:** Displays a standalone `Draft` node with an unknown author.<br>• **Warnings:** *"Low Confidence: Source is a Draft handover note with no official owner."* |
| **`Kilometervergoeding`** | Cross-Border Tax Mismatch | • **Answer:** Distinguishes between Belgian rate allowances (€0.44/km) and Dutch fiscal caps (€0.23/km).<br>• **Trust Score:** ~70–80%<br>• **Graph UI:** Shows conflicting node branches for BE and NL helpdesk channels. |

---

## 📊 Understanding the Results Panel

When a query is submitted, the UI presents four key deliverables:

1. **Synthesized Answer**: A direct, natural-language answer incorporating retrieved knowledge.
2. **Trust Score Badge**: An overall confidence indicator (0–100%) calculated dynamically based on source authority, recency, and active conflicts.
3. **Interactive Subgraph**: A visual node-and-edge map displaying the underlying documents, chats, topics, and relationship links (e.g., `SUPERSEDES`, `CONTRADICTS`).
4. **Source Citations & Flags**: Itemized text chunks showing the original source file, timestamp, author, and specific trust flags (e.g., *Informal Chat*, *Outdated*, *Draft*).
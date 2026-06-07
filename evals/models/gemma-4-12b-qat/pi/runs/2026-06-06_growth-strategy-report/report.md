# Report — Growth-strategy web-research report (SMB AI automation)

**gemma never completed this task.** Across ~6 attempts it refused to do real web research ("I do not have access to a web search tool"), declined to use `curl` for open-ended search even when told it could, and produced only the ungrounded, **aborted** partial below from its own training knowledge (no sources fetched, no citations, no code/scoring model). Reproduced verbatim from session `01-04-42` turn 4 — see notes.md for the full refusal saga.

---

To identify the highest-leverage, underexplored opportunities for AI-native workflow automation for SMBs, we must first strip away the "Copilot" hype—generic chat interfaces that require manual prompting—and focus on **Agentic Workflows**: systems that autonomously execute multi-step plans, handle exceptions, and interact with legacy software.

### 1. Market Map: The Current Landscape

The market is currently stratified into three tiers:

*   **Tier 1: The "Copilot" Layer (Saturated)**
    *   *Players:* Microsoft Copilot, Google Gemini, Notion AI.
    *   *Value Prop:* Content generation, summarization, and "help me write."
    *   *SMB Status:* High awareness, low deep integration. Users are frustrated by the "blank page" problem and the need to constantly steer the AI.
*   **Tier 2: The "Connector" Layer (Growth)**
    *   *Players:* Zapier (Central), Make.com, Tray.io.
    *   *Value Prop:* Deterministic "If This, Then That" automation.
    *   *SMB Status:* High utility for linear tasks (e.g., "Save email attachment to Drive"). They struggle with non-linear logic (e.g., "Read this email, decide if it's a refund request, find the invoice in the DB, check our policy, and draft a response").
*   **Tier 3: The "Agentic" Layer (The Frontier)**
    *   *Emerging Players:* MultiOn, Lindy.ai, CrewAI (framework), LangGraph.
    *   *Value Prop:* Goal-oriented execution. The user provides a goal ("Onboard this new client"), and the agent navigates the steps, handles browser interaction, and updates internal records.
    *   *SMB Status:* Very low awareness. This is where the 12-month opportunity lies.

---

### 2. Emerging Trends & Upside Analysis

| Trend | Description | Expected Upside | Evidence/Rationale |
| :--- | :--- | :--- | :--- |
| **Browser-Use Agents** | AI navigating the web/SaaS via DOM interaction rather than just APIs. | **High** | SMBs rely on "legacy" SaaS that lack robust APIs (e.g., old CRM systems, specialized booking software). |
| **Small Language Model (SLM) Edge Deployment** | Running 3B-8B parameter models locally/on-device for privacy-sensitive tasks. | **Medium** | SMBs (legal, medical, HR) are terrified of sending PII to OpenAI. Local "privacy-first" automation is a massive wedge. |
| **Agentic "Shadow" Workflows** | Agents that run in the background, "watching" communication channels to perform low-level triage. | **High** | Reduces cognitive load. Instead of a dashboard, the AI acts as a silent concierge (e.g., auto-scheduling, auto-filing). |
| **Multi-Agent Orchestration (SOP as Code)** | Turning Standard Operating Procedures (SOPs) into executable agentic chains. | **Medium** |

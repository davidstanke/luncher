# 🍽️ Luncher: Multi-Agent Orchestration Engine

Luncher is an enterprise multi-agent application built on the **Google Agent Development Kit (ADK) v2** and **Agent-to-Agent (A2A) protocol**.

It coordinates strategy-aligned team lunch meetings by orchestrating specialized capabilities:
- 👑 **Luncher Orchestrator** (`luncher_agent`): The primary user-facing frontend agent that coordinates tasks with sub-agents and synthesizes cohesive recommendations.
  - 🎯 **Strategy Subagent** (`strategy_agent`): In-process subagent that analyzes corporate strategy documents and product launch roadmaps.
  - 📅 **Scheduling Subagent** (`scheduling_agent`): In-process subagent that evaluates team member availability, calendars, and bookings.
- 🥪 [UNIMPLEMENTED] **Catering Agent** (`cater_agent`): Remote A2A peer connecting to catering menu service to suggest food for meetings.
---

## 💻 Reading This Guide in VS Code

The architecture diagram below is a mermaid block, and the setup sections that
follow are largely copy-paste shell commands. Two extensions make both usable:

- **[Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid)** (`bierner.markdown-mermaid`) — renders the diagrams instead of showing their source.
- **[Markdown Code Copy Button](https://marketplace.visualstudio.com/items?itemName=barnim.markdown-code-copy-button)** (`barnim.markdown-code-copy-button`) — adds a copy button to every code block.

Both are listed in `.vscode/extensions.json`, so VS Code offers them the first
time you open the repo. To install them directly:

```bash
code --install-extension bierner.markdown-mermaid
code --install-extension barnim.markdown-code-copy-button
```

Open this file in the preview pane with `Cmd+Shift+V` (`Ctrl+Shift+V` on Windows
and Linux).

---

## 🏛️ Agent Architecture Diagram

The orchestrator executes an ADK 2.0+ `Workflow` graph:
- **Intent Router**: Classifies the prompt into planning vs booking intents.
- **Planning Path (Parallel Gathering & Synthesis)**: Concurrently dispatches requests to in-process subagents `strategy_agent` and `scheduling_agent`, joins their outputs via `JoinNode`, and passes the combined context to `lunch_synthesizer` to deterministically format the structured Markdown proposal.
- **Booking Path (Direct Delegation)**: Routes selection/confirmation turns directly to `booking_handler` which delegates booking execution to `scheduling_agent`.

```mermaid
graph TD
    User(["👤 User / Client"]) -->|1. Sends Prompt| LuncherWorkflow

    subgraph LuncherWorkflow ["👑 Luncher Orchestrator (ADK 2.0 Workflow)"]
        Router["intent_router<br/>(Gemini Intent Classifier)"]
        StratSubagent["🎯 Strategy Subagent<br/><code>strategy_agent</code><br/>• inspect_strategy_documents()"]
        SchedSubagent["📅 Scheduling Subagent<br/><code>scheduling_agent</code><br/>• get_team_members()<br/>• book_meeting()<br/>• get_bookings()<br/>• cancel_booking()"]
        JoinGatherer["join_info_gatherer (JoinNode)"]
        Synthesizer["lunch_synthesizer<br/>format_lunch_proposal → Markdown"]
        BookingHandler["booking_handler<br/>(Booking Delegation)"]

        Router -->|Route: plan| StratSubagent
        Router -->|Route: plan| SchedSubagent
        Router -->|Route: book| BookingHandler
        BookingHandler -->|Delegate| SchedSubagent
        StratSubagent -->|Strategic Context| JoinGatherer
        SchedSubagent -->|Availability & Bookings| JoinGatherer
    end

    GCS[("🗄️ Cloud Storage / data/docs/<br/>gs://$PROJECT_ID-strategy-docs/")]
    MemBank[("🧠 Memory Bank / In-Process")]
    TeamData[("👥 data/team_members.json")]

    StratSubagent -->|PDF Document Read| GCS
    SchedSubagent -->|Team Roster Read| TeamData
    SchedSubagent -->|Team bookings| MemBank

    JoinGatherer -->|Combined Context Handoff| Synthesizer
    Synthesizer -->|Structured Markdown Proposal| User
    BookingHandler -->|Booking Confirmation| User
```
---

## Getting Started

### 1. 🛠️ Setup & Initialization
See: [Setup](docs/1_setup.md)

### 2. 💻 Running & Testing Agents Locally
See: [Local testing](docs/2_local.md)

### 3. ☁️ Deploying to Cloud & Agent Platform Playground
See: [Deploying to Cloud](docs/3_deploy.md)

### 4. 🥪 Extending Luncher with a catering agent
See: [Adding the catering agent](docs/4_cater_agent.md)

### 5. ✨ Registering to Gemini Enterprise
See: [Registering to Gemini Enterprise](docs/5_ge.md)

### 6. 🛡️ Enterprise Hardening (Agent Gateway, Model Armor & Agent Registry)
See: [Enterprise Hardening](docs/6_gateway_registry.md)

### 7. 🧹 Cleanup
See: [Cleanup](docs/7_cleanup.md)

---

| 🏠 Overview | [📚 Getting Started](#getting-started) | [Start: 1. Setup & Initialization ➡️](docs/1_setup.md) |
| :--- | :---: | ---: |
# 🛰️ Luncher Orchestrator Agent

The centralized Orchestrator Agent (the cognitive frontend) for the Luncher platform. It embeds both `strategy_agent` (Strategy Subagent) and `scheduling_agent` (Scheduling Subagent) as internal in-process subagents, and coordinates with `cater_agent` using the Google Agent Development Kit (ADK) and the Agent-to-Agent (A2A) protocol.

---

## 🏗️ Architecture

The Orchestrator acts as the "cognitive frontend" or user gateway, coordinating specialized sub-tasks:
1. **`strategy_agent`**: In-process subagent that analyzes corporate strategy documents (from `data/docs/` or GCS bucket `STRATEGY_DOCS_BUCKET`) and extracts strategic goals and active initiatives.
2. **`scheduling_agent`**: In-process subagent that evaluates team members' weekly availability (from `data/team_members.json`), checks existing bookings, and records/cancels bookings in the Memory Bank (or in-process calendar).
3. **`cater_agent`** *(extensible)*: Queried via A2A to recommend catering options from BigQuery menus.

---

## ☁️ Deployment Target

`luncher_agent` deploys to **Agent Runtime** (`deployment_target: agent_runtime`). It serves reasoning engine routes, A2A endpoints, and the agent card. See the root `README.md` and `docs/3_deploy.md` for the deployment sequence.

---

## 🚀 Local Development & Execution

Start the orchestrator agent from the repository root. `main.py` defaults to port 8080:

```bash
uv --directory agents/luncher_agent run main.py
```

Then open the dev UI:

```
http://localhost:8080
```

then prompt the orchestrator, e.g.

```
Plan a team lunch meeting for next week that aligns with our corporate strategy.
```

The orchestrator replies with a structured Markdown lunch proposal including strategic rationale, team roster, ranked time slots with attendance counts, and a recommended option.

To book, reply directly in chat with your preferred slot (e.g., *"Book Tuesday 12:00"* or *"Option 1 works"*). The agent will book the meeting and return a confirmation with the booking details and food reminder.

> **Note:** use `main.py`, not `adk web`. Both serve the same ADK dev UI, but `adk web`
> builds its own app via the ADK CLI and therefore skips `app/fast_api_app.py` — so the
> A2A endpoints, the agent card and `/feedback` would not be served.

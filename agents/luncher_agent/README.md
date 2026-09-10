# 🛰️ Luncher Orchestrator Agent

The centralized Orchestrator Agent (the cognitive frontend) for the Luncher platform. It embeds both `strategy_agent` (Strategy Subagent) and `scheduling_agent` (Scheduling Subagent) as internal in-process subagents, with an extensible student exercise for `catering_agent` using the Google Agent Development Kit (ADK).

---

## 🏗️ Architecture

The Orchestrator acts as the "cognitive frontend" or user gateway, coordinating specialized sub-tasks:
1. **`strategy_agent`**: In-process subagent that analyzes corporate strategy documents (from `data/docs/` or GCS bucket `STRATEGY_DOCS_BUCKET`) and extracts strategic goals and active initiatives.
2. **`scheduling_agent`**: In-process subagent that evaluates team members' weekly availability (from `data/team_members.json`), checks existing bookings, and records/cancels bookings in the Memory Bank (or in-process calendar).
3. **`catering_agent`** *(student extension)*: In-process subagent recommending catering options from BigQuery menus.

---

## ☁️ Deployment Target

`luncher_agent` deploys to **Agent Runtime** (`deployment_target: agent_runtime`). It serves reasoning engine routes, ADK dev UI, and `/feedback`. See the root `README.md` and `docs/3_deploy.md` for the deployment sequence.

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

> **Note:** Use `main.py`, not `adk web`. Both serve the same ADK dev UI, but `main.py`
> starts `app/fast_api_app.py` with production telemetry, reasoning engine routes, and `/feedback`.

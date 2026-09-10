# Extend Luncher with integration to catering menu service

This is your task, with help from Antigravity. Build a subagent that provides lunch menu options for scheduled meetings, pulled from the company's in-house catering service. Menu options are stored in BigQuery and can be accessed via MCP.

You will implement this capability as an internal, in-process subagent—`catering_agent`—inside `luncher_agent` (matching the architecture of `strategy_agent` and `scheduling_agent`).

## Prerequisites

Ensure that you have the [`agents-cli` skills](https://github.com/google/agents-cli) and workspace plugins installed in Antigravity.

* **Antigravity 2.0:** Go to _Settings > Customizations_ and confirm that several `google-agents-cli-*` skills and the `eval-viewer` plugin are listed.
* **Antigravity CLI:** At the prompt, enter `/skills` and confirm that `google-agents-cli-*` and `eval-viewer` skills are listed.

---

## Step 1. Create the subagent

### 1.1. Subagent scaffolding & workflow wiring

Initiate a `/grill-me` session, then enter the following prompt and answer any questions:

```
Inside `agents/luncher_agent/app/`, create a new in-process subagent module named `catering_agent.py`.
Its purpose is to provide catering menu options to serve at a lunch meeting.

1. In `agents/luncher_agent/app/catering_agent.py`:
   - Define `catering_agent = Agent(name="catering_agent", ...)` using Google ADK.
   - For the initial version, DO NOT implement any actual retrieval of menu items. Instead, have the agent return three mock menu suggestions:
     - Menu 1: {buffalo chicken wrap, mixed greens salad, chocolate cookie, assorted sodas}
     - Menu 2: {veggie tacos, snow pea salad, apple tartlets, tea service}
     - Menu 3: {lamb vindaloo, spiced cauliflower, naan, orange-mint spa water}

2. In `agents/luncher_agent/app/agent.py`:
   - Import `catering_agent` from `.catering_agent`.
   - Update the workflow edges so that `catering_agent` runs in parallel with `strategy_agent` and `scheduling_agent`:
     - Change the "plan" branch: `("plan": (strategy_agent, scheduling_agent, catering_agent))`
     - Change the join node inputs: `((strategy_agent, scheduling_agent, catering_agent), join_info_gatherer)`

3. In `agents/luncher_agent/app/proposal_builder.py`:
   - Update the synthesizer instruction and `format_lunch_proposal` tool so the synthesized proposal includes catering menu recommendations alongside strategy alignment and available timeslots.
```

### 1.2. Run locally

If the local auto-reloading server is already running via `watchfiles`, it will automatically detect the new files and reload. Otherwise, start `luncher_agent` locally:

```
Kill any process on port 8080, then start luncher_agent locally.
```

Or run directly in terminal:

```bash
uv --directory agents/luncher_agent run main.py
```

### 1.3. Validate local agent

Visit [http://localhost:8080/dev-ui/?app=luncher_agent](http://localhost:8080/dev-ui/?app=luncher_agent) and enter a prompt, like `plan a lunch meeting for tuesday`. Verify that the application continues to function and now includes catering menu options in the synthesized lunch proposal.

---

## Step 2. First deployment

### 2.1. Deploy to Agent Runtime

Deploy `luncher_agent` (which now packages `strategy_agent`, `scheduling_agent`, and `catering_agent` as in-process subagents) to Agent Platform's Agent Runtime with telemetry enabled:

```
Deploy luncher_agent to Agent Platform's Agent Runtime with telemetry and prompt/response logging enabled.
```

Alternatively, you can run the deployment command directly:

```bash
source .env

BASE_ENV="GOOGLE_GENAI_MODEL=${GOOGLE_GENAI_MODEL},GOOGLE_GENAI_LOCATION=${GOOGLE_GENAI_LOCATION},GOOGLE_CLOUD_PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID},GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}"
AGENT_SETTINGS_ENV="GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true,OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true,OTEL_SEMCONV_STABILITY_OPT_IN=default"

uv --directory agents/luncher_agent run agents-cli deploy \
  --project "$GOOGLE_CLOUD_PROJECT_ID" \
  --region "$GOOGLE_CLOUD_LOCATION" \
  --agent-identity \
  --update-env-vars "$BASE_ENV,$AGENT_SETTINGS_ENV${STRATEGY_DOCS_BUCKET:+,STRATEGY_DOCS_BUCKET=$STRATEGY_DOCS_BUCKET},BIGQUERY_LOCATION=${BIGQUERY_LOCATION}"
```

### 2.2. Validate deployed agent

When the deployment completes, open the deployed `luncher_agent` on Agent Runtime / Gemini Enterprise and confirm that the catering options are presented in the generated proposals.

---

## Step 3. Access catering data via MCP

### 3.1. Initialize and review BigQuery dataset

Run the BigQuery seed script to create the `catering` dataset and populate the `menu_items` table:

```bash
./scripts/04-cater-agent-bq-seed.sh
```

In Google Cloud console, visit **BigQuery** and find dataset `catering`. Within that dataset, inspect table `menu_items`. Query it to explore the catering dishes, categories, and allergen data it contains.

### 3.2. Add MCP connectivity

Initiate a `/grill-me` session, then enter the following prompt and answer any questions:

```
Add a tool to `catering_agent` named `fetch_catering_data` in `agents/luncher_agent/app/cater_tools.py` (or directly in `catering_agent.py`).
It should connect to the GCP MCP endpoint for BigQuery, and use that server's `execute_sql` tool to query dataset/table `catering:menu_items` (in the same project that the agent is running in).

`fetch_catering_data` should return three proposed menus, each of which includes a main dish, a side, dessert, and beverage. Attempt to make each menu thematically consistent.

Update `propose_lunch` and synthesizer methods to use the dynamically-fetched menu suggestions instead of mock data.
```

### 3.3. Test local agent

When the implementation is complete, visit [http://localhost:8080/dev-ui/?app=luncher_agent](http://localhost:8080/dev-ui/?app=luncher_agent) and enter a prompt, like `plan a lunch meeting for tuesday`. Verify that the application continues to function, and that catering options are now dynamically generated from BigQuery.

### 3.4. Redeploy

Redeploy `luncher_agent` with the new BigQuery tool:

```
Redeploy luncher_agent with telemetry and prompt/response logging enabled.
```

Or run the deployment command directly:

```bash
source .env
BASE_ENV="GOOGLE_GENAI_MODEL=${GOOGLE_GENAI_MODEL},GOOGLE_GENAI_LOCATION=${GOOGLE_GENAI_LOCATION},GOOGLE_CLOUD_PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID},GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}"
AGENT_SETTINGS_ENV="GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true,OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true,OTEL_SEMCONV_STABILITY_OPT_IN=default"

uv --directory agents/luncher_agent run agents-cli deploy \
  --project "$GOOGLE_CLOUD_PROJECT_ID" \
  --region "$GOOGLE_CLOUD_LOCATION" \
  --agent-identity \
  --update-env-vars "$BASE_ENV,$AGENT_SETTINGS_ENV${STRATEGY_DOCS_BUCKET:+,STRATEGY_DOCS_BUCKET=$STRATEGY_DOCS_BUCKET},BIGQUERY_LOCATION=${BIGQUERY_LOCATION}"
```

### 3.5. Validate deployed agent

When deployment completes, visit the deployed `luncher_agent` on Agent Runtime / Gemini Enterprise and confirm that catering options are dynamically retrieved from BigQuery.

---

## Step 4. Store user preferences as memories

### 4.1. Add memory tools

Initiate a `/grill-me` session, then enter the following prompt and answer any questions:

```
Add a memory feature for dietary preferences. Requirements:
- When luncher_agent receives a prompt that specifies a dietary preference (e.g. "my team doesn't eat pork" or "I am gluten-free"), route or save this preference directly.
- catering_agent has a tool for storing user dietary preferences as memories.
- When deployed to Agent Runtime, memories are stored using GEAP Memory Bank.
- When running locally, memories are stored in an in-process local memory store (matching the pattern in bookings.py).
- Before querying for menus, consult the memory service for any stored dietary preferences.
- Filter menu suggestions accordingly to present only menus that attendees will enjoy.
- When the final response is delivered to the user, append text: "Are there any dietary preferences that I should consider? Specify them and I'll remember them for the future."
```

### 4.2. Validate local agent

When the implementation is complete, visit [http://localhost:8080/dev-ui/?app=luncher_agent](http://localhost:8080/dev-ui/?app=luncher_agent) and enter a preference prompt, like `my team doesn't like fish`. Verify that the application records the preference and filters subsequent catering options accordingly.

> **Note:** When running locally without Agent Runtime Memory Bank, memories are preserved in-process for the life of the local server session.

### 4.3. Redeploy

Redeploy `luncher_agent`:

```bash
uv --directory agents/luncher_agent run agents-cli deploy \
  --project "$GOOGLE_CLOUD_PROJECT_ID" \
  --region "$GOOGLE_CLOUD_LOCATION" \
  --agent-identity \
  --update-env-vars "$BASE_ENV,$AGENT_SETTINGS_ENV${STRATEGY_DOCS_BUCKET:+,STRATEGY_DOCS_BUCKET=$STRATEGY_DOCS_BUCKET},BIGQUERY_LOCATION=${BIGQUERY_LOCATION}"
```

---

## Step 5. Add evaluations

Validate `catering_agent` using the `agents-cli eval` framework to test that it reliably generates themed menus, adheres to dietary constraints, and records memory preferences. This supports local developer iteration, regression testing, and cloud monitoring on Gemini Enterprise Agent Platform (GEAP).

### 5.1. Evaluation scaffolding

Initiate a `/grill-me` session, then enter the following prompt and answer any questions:

```
In `agents/luncher_agent/tests/eval`, extend the evaluation suite:

1. Create dataset `tests/eval/datasets/catering-dataset.json` with evaluation cases covering:
   - Basic menu proposal: Requesting catering menu options for a lunch meeting and verifying 3 themed 4-course menus (main, side, dessert, beverage) are returned.
   - Dietary restrictions filtering: Requesting menus with constraints (e.g., vegetarian, gluten-free, no seafood/fish) and ensuring returned items strictly follow the restrictions.
   - Preference memory storage: Storing dietary preferences when prompted rather than attempting to schedule a meeting.

2. In `tests/eval/eval_config.yaml`, add:
   - `dietary_filtering`: Custom metric validating that all returned menus strictly adhere to requested dietary and allergen restrictions.

3. Implement the custom evaluator function in `tests/eval/dietary_filtering.py`.
```

### 5.2. Local developer loop

During local development, generate execution traces against your running agent on port 8080 and score them against your evaluation configuration.

#### 5.2.1. Launch the evaluation dashboard sidecar (optional)

The workspace includes an Antigravity sidecar plugin in `.agents/plugins/eval-viewer` that serves an interactive HTML dashboard and scorecard viewer on port **8088**.

You can prompt Antigravity to start the sidecar:

```
Start the eval-viewer sidecar server.
```

#### 5.2.2. Run evaluation traces and grading

You can prompt Antigravity to run the local evaluation flow:

```
Run the eval suite for catering integration:
1. Ensure the local luncher_agent server is running on port 8080.
2. Run `agents-cli eval generate` against http://localhost:8080 using `tests/eval/datasets/catering-dataset.json` and `--app-name luncher_agent`.
3. Grade the latest trace using `tests/eval/eval_config.yaml`.
4. Output the score summary table and link to the grade results.
```

Alternatively, you can execute `agents-cli` commands directly:

```bash
# Generate traces from the local luncher_agent
uv --directory agents/luncher_agent run agents-cli eval generate \
  --dataset tests/eval/datasets/catering-dataset.json \
  --url http://localhost:8080 \
  --app-name luncher_agent

# Grade the generated traces against eval_config.yaml
uv --directory agents/luncher_agent run agents-cli eval grade \
  --traces artifacts/traces/ \
  --config tests/eval/eval_config.yaml
```

### 5.3. Analyze evaluation results and iterate (Quality Flywheel)

Review grade results to diagnose failures, adjust instructions or tools, and compare runs against your baseline to ensure scores improve without regressions.

You can prompt Antigravity to analyze results and iterate on fixes:

```
Analyze the latest eval results for catering integration against our baseline:
1. Identify the latest evaluation result in `agents/luncher_agent/artifacts/grade_results/`.
2. Compare candidate run against the baseline using `agents-cli eval compare`.
3. If any evaluation case failed or regressed:
   - Identify the root cause from judge rationales and trace data.
   - Propose and apply fixes to catering_agent instructions or tool logic.
   - Re-run evaluation and verify scores meet or exceed baseline.
4. Show the final scorecard and comparison summary.
```

Or manually inspect and compare runs:

1. **Review Grade Results:**
   Visit the local evaluation dashboard at **http://localhost:8088** (or open the generated HTML report in `agents/luncher_agent/artifacts/grade_results/results_<timestamp>.html`) to inspect scorecards, judge explanations, and individual case traces.

2. **Diagnose and Fix Failures:**
   - **Low `dietary_filtering` score:** If excluded allergens appear in suggestions, adjust the system instructions in `app/catering_agent.py` or enhance SQL query and memory filtering logic in `app/cater_tools.py`.
   - **Low `custom_response_quality` score:** If menus lack 4 courses or miss thematic consistency, clarify prompt instructions in `app/catering_agent.py` or `app/proposal_builder.py`.

3. **Compare Results Against Baseline:**

   ```bash
   export EVAL_BASELINE="tests/eval/baselines/baseline_results.json"
   export EVAL_NEW=$(ls -t agents/luncher_agent/artifacts/grade_results/results_*.json | head -n 1 | sed 's|agents/luncher_agent/||')

   uv --directory agents/luncher_agent run agents-cli eval compare \
     "$EVAL_BASELINE" \
     "$EVAL_NEW"
   ```

### 5.4. Cloud evaluation and monitoring on Gemini Enterprise Agent Platform (GEAP)

For deployed agents on Agent Runtime, you can evaluate live conversation sessions, benchmark experiments, and define evaluation criteria directly in the **Google Cloud Console > Agent Platform > Evaluation** dashboard:

- **Online Monitoring:** Open **[Google Cloud Console > Agent Platform > Evaluation > Online Monitoring](https://console.cloud.google.com/vertex-ai/evaluation/online-monitoring)** to inspect continuous real-time score distributions and latency.
- **Cloud Trace Explorer:** Navigate to **[Google Cloud Console > Trace > Trace explorer](https://console.cloud.google.com/traces/explorer)** to inspect end-to-end request latency across in-process subagents and BigQuery MCP queries.

---

## Step 6. (optional). Learn from experience

Run `/learn` and follow the prompts to help Antigravity improve based on learnings from this session.

---

## Step 7. Cleanup

### 7.1. Stop local servers

Enter the following prompt to stop local background processes:

```
Stop all locally running agents and processes.
```

---

| [⬅️ Previous: 3. Deploying to Cloud & Agent Platform Playground](3_deploy.md) | [📚 Getting Started](../README.md#getting-started) | [Next: 5. Registering to Gemini Enterprise ➡️](5_ge.md) |
| :--- | :---: | ---: |

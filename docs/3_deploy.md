# Deploying agents to Google Cloud

Once tested locally, deploy your agents to **Gemini Enterprise Agent Platform (GEAP) Agent Runtime** and interact with them in the Cloud Console. All deployment commands below execute directly from the repository root.

## Multi-Agent Agent Descriptions

The system coordinates specialized capabilities to plan strategy-aligned team lunches. `strategy_agent` and `scheduling_agent` operate directly as in-process subagents within `luncher_agent`, with `catering_agent` to be added as an in-process subagent in the next chapter:

| Agent | Directory / Name | Role & Description | Deployment Target | Connecting Tools / Subagents |
| :--- | :--- | :--- | :--- | :--- |
| 👑 **Luncher Orchestrator** | `luncher_agent` | **Primary Workflow Coordinator**: Orchestrates end-to-end lunch planning across sub-agents in a 2-stage pipeline (parallel gathering then synthesis). | **Agent Runtime** (`agents-cli deploy` with `--agent-identity`) | • **Internal Subagents**: `strategy_agent` (reads PDFs from GCS bucket `gs://${STRATEGY_DOCS_BUCKET}` or local `data/docs/`), `scheduling_agent` (evaluates team availability and records team bookings in Memory Bank)<br>• **Student Extension**: `catering_agent` (upcoming)<br>• **Internal Agent**: `lunch_synthesizer`<br>• **Tools**: `format_lunch_proposal_tool` |
| 🥪 **Catering Subagent** *(Upcoming)* | `catering_agent` | **Catering & Dietary Coordinator**: Suggests balanced, themed lunch menus and records/filters team dietary preferences. *(To be built from scratch as an in-process subagent).* | **Agent Runtime** (packaged within `luncher_agent`) | • **Tools**: `fetch_catering_data` (BigQuery `catering.menu_items` via MCP `execute_sql`), dietary preference memory tools<br>• **Storage**: Reasoning Engine Memory Bank (dietary preferences)<br>• **Subagent of**: `luncher_agent` |

> **NOTE**
>
> **Catering Subagent Development:** We will come back to the Catering Subagent (`catering_agent`) and build it up from scratch in a dedicated implementation phase (see [Adding the catering subagent](4_cater_agent.md)).

> **NOTE**
>
> Why agents deploy to Agent Runtime:
>
> - **Injected Memory Bank Engine:** `luncher_agent` stores team bookings in Memory Bank (`reasoningEngines/<ENGINE_ID>`). Agent Runtime automatically injects `GOOGLE_CLOUD_AGENT_ENGINE_ID`, so the host *is* the memory host without needing separate engine infrastructure.
> - **Agent Identity (`--agent-identity`):** Deploys agents with Workload Identity Federation, granting runtime permissions to GCP resources (GCS, BigQuery, and Reasoning Engines) via the project's Principal Set.
> - **Orchestrator Hosting:** `luncher_agent` deploys directly to Agent Runtime, serving both ADK reasoning engine routes and dev UI seamlessly.

---

## Deploying the agents to GEAP Agent Runtime

### Step 1: Load the environment

Every deployed agent gets these environment variables in their runtime. `BASE_ENV` configures project and model connectivity, while `AGENT_SETTINGS_ENV` enables runtime telemetry and prompt/response logging required for GEAP Cloud evaluations.

```bash
source .env

BASE_ENV="GOOGLE_GENAI_MODEL=${GOOGLE_GENAI_MODEL},GOOGLE_GENAI_LOCATION=${GOOGLE_GENAI_LOCATION},GOOGLE_CLOUD_PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID},GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}"

AGENT_SETTINGS_ENV="GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true,OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true,OTEL_SEMCONV_STABILITY_OPT_IN=default"
```

### Step 2 (Optional): Serve the strategy PDFs from Cloud Storage

The internal `strategy_agent` inside `luncher_agent` reads PDFs from local `data/docs/`, unless `STRATEGY_DOCS_BUCKET` names a bucket. Same image, same code; one variable picks the branch. Skippable for local testing, but recommended when deploying `luncher_agent` to Agent Runtime.

```bash
export STRATEGY_DOCS_BUCKET="${GOOGLE_CLOUD_PROJECT_ID}-strategy-docs"

gcloud storage buckets create "gs://${STRATEGY_DOCS_BUCKET}" \
  --project "$GOOGLE_CLOUD_PROJECT_ID" --location "$GOOGLE_CLOUD_LOCATION"

gcloud storage cp data/docs/*.pdf "gs://${STRATEGY_DOCS_BUCKET}/"

gcloud storage buckets add-iam-policy-binding "gs://${STRATEGY_DOCS_BUCKET}" \
  --member "serviceAccount:service-$(gcloud projects describe "$GOOGLE_CLOUD_PROJECT_ID" --format='value(projectNumber)')@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role roles/storage.objectViewer

gcloud storage ls "gs://${STRATEGY_DOCS_BUCKET}"
```

The grant goes to the **Agent Runtime service agent** (`gcp-sa-aiplatform-re`),
which `03-setup-iam.sh` provisions — so run this after it. The `ls` should list
eight PDFs. The orchestrator deploy below picks the variable up when set.

### Step 3: Deploy the Luncher Agent (`luncher_agent`) to Agent Runtime

Deploy `luncher_agent` with Agent Identity and pass `STRATEGY_DOCS_BUCKET` so `strategy_agent` reads the corporate strategy PDFs from Cloud Storage:

```bash
uv --directory agents/luncher_agent run agents-cli deploy \
  --project "$GOOGLE_CLOUD_PROJECT_ID" \
  --region "$GOOGLE_CLOUD_LOCATION" \
  --agent-identity \
  --update-env-vars "$BASE_ENV,$AGENT_SETTINGS_ENV${STRATEGY_DOCS_BUCKET:+,STRATEGY_DOCS_BUCKET=$STRATEGY_DOCS_BUCKET}"
```

> **NOTE**
>
> This engine also hosts the bookings Memory Bank. Deploys take 5-10 min; add `--no-wait` and poll `agents-cli deploy --status` if the command may time out.

### Step 4: Manual testing of deployed agent
Test the orchestrator agent:

- visit [Deployments on Agent Runtime](https://console.cloud.google.com/agent-platform/runtimes) and navigate to "luncher-agent"
- Click "Playground"
- enter a prompt like `Schedule a lunch meeting for Monday`
- Or query via CLI:
  ```bash
  ENGINE_ID=$(jq -r '.remote_agent_runtime_id | split("/") | last' agents/luncher_agent/deployment_metadata.json)
  uv --directory agents/luncher_agent run agents-cli run \
    --url "https://${GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com/v1/projects/${GOOGLE_CLOUD_PROJECT_ID}/locations/${GOOGLE_CLOUD_LOCATION}/reasoningEngines/${ENGINE_ID}" \
    --mode adk "Plan an executive strategy lunch for next Tuesday for the team."
  ```

> **NOTE**
>
> We will come back to `catering_agent` and build it up from scratch following [`4_cater_agent.md`](4_cater_agent.md).

---

| [⬅️ Previous: 2. Local Testing](2_local.md) | [📚 Getting Started](../README.md#getting-started) | [Next: 4. Extending Luncher with a catering subagent ➡️](4_cater_agent.md) |
| :--- | :---: | ---: |

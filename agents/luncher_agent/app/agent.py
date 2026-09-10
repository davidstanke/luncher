# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
from typing import Any, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import (
    HttpRetryOptions,
    ThinkingConfig,
    ThinkingLevel,
)

from google.adk.agents import Agent
from google.adk.agents.context import Context
from google.adk.apps.app import App
from google.adk.events.event import Event
from google.adk.models.google_llm import Gemini
from google.adk.workflow import JoinNode, Workflow, node

from .proposal_builder import (
    ROLE_DESCRIPTION as SYNTHESIZER_INSTRUCTION,
    format_lunch_proposal_tool,
)
from .strategy_agent import strategy_agent
from .scheduling_agent import scheduling_agent

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "WARNING").upper())
logger = logging.getLogger(__name__)

# Load environment variables
# override=True: a stale shell export must not beat .env.
load_dotenv(override=True)

# Gemini Enterprise Agent Platform (GEAP) & GCP Project configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_LOCATION = os.getenv("GOOGLE_GENAI_LOCATION", "global")
# Pinned version. Override via GOOGLE_GENAI_MODEL. Only served from the `global`
# endpoint -- regional locations return 404 for it.
MODEL = os.getenv("GOOGLE_GENAI_MODEL", "gemini-3.6-flash")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

logger.info("Using Gemini model '%s' in location '%s'", MODEL, MODEL_LOCATION)

default_retry_policy = HttpRetryOptions(
    attempts=5,
    initial_delay=2.0,
    max_delay=30.0,
    http_status_codes=[429, 500, 503],
)

class IntentClassification(BaseModel):
    intent: Literal["plan", "book"] = Field(
        description="The classified intent: 'plan' for planning/finding lunch times, 'book' for selecting/booking a specific slot."
    )


def _extract_text_from_input(content: Any) -> str:
    if isinstance(content, str):
        return content
    if hasattr(content, "parts") and content.parts:
        return " ".join(
            part.text for part in content.parts if getattr(part, "text", None)
        )
    if isinstance(content, dict):
        return str(content)
    return str(content) if content is not None else ""


@node(name="intent_router")
async def intent_router(ctx: Context, node_input: Any) -> Event:
    """Routes user messages between the planning and booking branches."""
    user_prompt = _extract_text_from_input(node_input)
    if not user_prompt.strip():
        return Event(output=node_input, route="plan")

    try:
        client = genai.Client()
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are an intent router for a team lunch coordination system. "
                    "Classify the user message into one of two intents:\n"
                    "- 'plan': The user wants to plan, schedule, coordinate, or find options for a team lunch.\n"
                    "- 'book': The user wants to select, confirm, or book a specific slot or proposal.\n"
                    "Default to 'plan' if ambiguous or general chat."
                ),
                response_mime_type="application/json",
                response_schema=IntentClassification,
            ),
        )
        parsed = IntentClassification.model_validate_json(response.text)
        route = parsed.intent
    except Exception as e:
        logger.warning("Intent router LLM failed, defaulting to 'plan': %s", e)
        lower = user_prompt.lower().strip()
        if lower.startswith(("book", "confirm", "reserve", "choose", "select")):
            route = "book"
        else:
            route = "plan"

    return Event(output=node_input, route=route)


@node(name="booking_handler", rerun_on_resume=True)
async def booking_handler(ctx: Context, node_input: Any) -> Any:
    """Delegates booking and selection turns directly to scheduling_agent."""
    return await ctx.run_node(
        scheduling_agent,
        node_input=node_input,
        use_as_output=True,
    )


# Proposal Synthesizer: synthesize corporate strategy and schedule into a structured Markdown proposal
synthesizer_agent = Agent(
    model=Gemini(
        model=MODEL,
        # Not MINIMAL: this agent reconciles sub-agent outputs and carries
        # the roster and per-slot free counts across verbatim. At MINIMAL it
        # intermittently rewrites the attendee list rather than copying it.
        thinking_config=ThinkingConfig(thinking_level=ThinkingLevel.LOW),
        retry_options=default_retry_policy,
        client_kwargs={"location": MODEL_LOCATION},
    ),
    name="lunch_synthesizer",
    description="Synthesizes corporate strategy objectives and scheduling options into a team lunch proposal.",
    instruction=SYNTHESIZER_INSTRUCTION,
    tools=[format_lunch_proposal_tool],
)

join_info_gatherer = JoinNode(name="join_info_gatherer")

# Root Orchestrator: ADK 2.0 Workflow coordinating intent routing, parallel data gathering, and booking
luncher_agent = Workflow(
    name="luncher_agent",
    description="The centralized Luncher Orchestrator that coordinates strategy-aligned team lunch meetings.",
    edges=[
        ("START", intent_router),
        (
            intent_router,
            {
                "plan": (strategy_agent, scheduling_agent),
                "book": booking_handler,
            },
        ),
        ((strategy_agent, scheduling_agent), join_info_gatherer),
        (join_info_gatherer, synthesizer_agent),
    ],
)

root_agent = luncher_agent

app = App(
    name="luncher_agent",
    root_agent=root_agent,
)



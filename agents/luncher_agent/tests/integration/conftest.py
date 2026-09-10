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

"""Integration test fixtures and helpers for luncher_agent."""

import logging
import os
import subprocess
import threading
import time
from collections.abc import Iterator
from typing import Any

import pytest
import requests
from requests.exceptions import RequestException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sessions would otherwise be written to the deployed agent's
# Agent Engine. Popped before anything imports app.app_utils.services, whose
# builders are cached on first call.
os.environ.pop("GOOGLE_CLOUD_AGENT_ENGINE_ID", None)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENTS_DIR = os.path.dirname(AGENT_DIR)


def log_output(pipe: Any, log_func: Any) -> None:
    """Log the output from the given pipe."""
    for line in iter(pipe.readline, ""):
        log_func(line.strip())


def tail_output(process: subprocess.Popen[str], tag: str) -> None:
    """Drain both pipes. An undrained PIPE hides startup tracebacks and fills."""
    threading.Thread(
        target=log_output,
        args=(process.stdout, lambda line: logger.info("[%s] %s", tag, line)),
        daemon=True,
    ).start()
    threading.Thread(
        target=log_output,
        args=(process.stderr, lambda line: logger.error("[%s] %s", tag, line)),
        daemon=True,
    ).start()


def wait_for_url(
    url: str,
    process: subprocess.Popen[str] | None = None,
    timeout: float = 30.0,
    poll: float = 0.5,
) -> bool:
    """Poll url until it returns 200 or the budget expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process and process.poll() is not None:
            logger.error("Process exited early with return code %d", process.returncode)
            return False
        try:
            if requests.get(url, timeout=1.0).status_code == 200:
                return True
        except RequestException:
            pass
        time.sleep(poll)
    return False

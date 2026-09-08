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

from unittest.mock import MagicMock, patch
import pytest
from google.adk.agents import Agent

from app.strategy_agent import inspect_strategy_documents, strategy_agent


def test_strategy_agent_properties() -> None:
    """Verifies strategy_agent definition, naming, and tool registration."""
    assert isinstance(strategy_agent, Agent)
    assert strategy_agent.name == "strategy_agent"
    assert "inspect_strategy_documents" in [t.__name__ for t in strategy_agent.tools]


def test_inspect_strategy_documents_local(monkeypatch) -> None:
    """Tests local PDF loading from candidate directories."""
    monkeypatch.delenv("STRATEGY_DOCS_BUCKET", raising=False)
    output = inspect_strategy_documents()
    assert isinstance(output, str)
    assert "--- Document (Local):" in output
    assert "OmniChef" in output or "VisionSphere" in output


def test_inspect_strategy_documents_missing_dir(monkeypatch) -> None:
    """Tests fallback when no candidate directories or PDFs exist."""
    monkeypatch.delenv("STRATEGY_DOCS_BUCKET", raising=False)
    with patch("os.path.exists", return_value=False):
        output = inspect_strategy_documents()
        assert "Local strategy documents directory not found" in output


def test_inspect_strategy_documents_empty_dir(monkeypatch, tmp_path) -> None:
    """Tests when local directory has no PDFs."""
    monkeypatch.delenv("STRATEGY_DOCS_BUCKET", raising=False)
    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=["notes.txt"]), \
         patch("os.path.isfile", return_value=True):
        output = inspect_strategy_documents()
        assert "No PDF documents found" in output


def test_inspect_strategy_documents_gcs_error(monkeypatch) -> None:
    """Tests error handling when GCS bucket read fails."""
    monkeypatch.setenv("STRATEGY_DOCS_BUCKET", "test-bucket")
    with patch("google.cloud.storage.Client", side_effect=Exception("Auth error")):
        with pytest.raises(RuntimeError) as exc_info:
            inspect_strategy_documents()
        assert "Cannot read STRATEGY_DOCS_BUCKET" in str(exc_info.value)

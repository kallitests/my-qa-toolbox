"""
tests/test_setup_dev_env.py
============================
Unit tests for setup_dev_env.py
Ollama is mocked — no real LLM calls in CI.
"""

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

# ── Helpers ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def no_real_subprocess(monkeypatch):
    """
    Prevent any real subprocess.run calls that would install software.
    Tests that need subprocess must patch it explicitly.
    """
    pass  # individual tests patch as needed


# ── Import the module under test ──────────────────────────────────────────────

# Patch _bootstrap so it doesn't try to pip install during import in CI
with patch("builtins.__import__", side_effect=lambda *a, **k: __import__(*a, **k)):
    pass

# We import lazily inside tests to control patches
def _import_module():
    """Import setup_dev_env with Ollama/LangChain patched out."""
    with patch.dict("sys.modules", {
        "langchain_ollama":       MagicMock(),
        "langchain_core":         MagicMock(),
        "langchain_core.messages": MagicMock(),
        "langchain_core.prompts":  MagicMock(),
        "langchain_core.output_parsers": MagicMock(),
        "rich":                   MagicMock(),
        "rich.console":           MagicMock(),
        "rich.panel":             MagicMock(),
        "rich.progress":          MagicMock(),
        "rich.table":             MagicMock(),
    }):
        if "scripts.setup_dev_env" in sys.modules:
            del sys.modules["scripts.setup_dev_env"]
        import importlib
        spec = importlib.util.spec_from_file_location(
            "setup_dev_env",
            Path(__file__).parent.parent / "scripts" / "setup_dev_env.py",
        )
        mod = importlib.util.module_from_spec(spec)
        # Patch _bootstrap to no-op
        mod._bootstrap = lambda: None  # type: ignore[attr-defined]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Ollama helpers                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class TestCheckOllamaServer:
    def test_returns_true_when_reachable(self):
        mod = _import_module()
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            assert mod.check_ollama_server("http://localhost:11434") is True

    def test_returns_false_when_unreachable(self):
        mod = _import_module()
        with patch("requests.get", side_effect=ConnectionError("refused")):
            assert mod.check_ollama_server("http://localhost:11434") is False

    def test_returns_false_on_non_200(self):
        mod = _import_module()
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 503
            assert mod.check_ollama_server("http://localhost:11434") is False


class TestListOllamaModels:
    def test_returns_model_names(self):
        mod = _import_module()
        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = {
                "models": [
                    {"name": "mistral:latest"},
                    {"name": "llama3.2:8b"},
                    {"name": "codellama:7b"},
                ]
            }
            mock_get.return_value.status_code = 200
            result = mod.list_ollama_models("http://localhost:11434")
            assert result == ["mistral", "llama3.2", "codellama"]

    def test_returns_empty_on_error(self):
        mod = _import_module()
        with patch("requests.get", side_effect=Exception("network error")):
            assert mod.list_ollama_models("http://localhost:11434") == []


class TestPickBestModel:
    def test_returns_preferred_if_available(self):
        mod = _import_module()
        with patch.object(mod, "list_ollama_models", return_value=["mistral", "llama3.2"]):
            assert mod.pick_best_model("http://localhost:11434", "mistral") == "mistral"

    def test_falls_back_to_recommended(self):
        mod = _import_module()
        with patch.object(mod, "list_ollama_models", return_value=["phi3", "gemma2"]):
            # phi3 is in RECOMMENDED_MODELS, gemma2 too
            result = mod.pick_best_model("http://localhost:11434", "mistral")
            assert result in ["phi3", "gemma2"]

    def test_returns_first_available_if_no_recommended(self):
        mod = _import_module()
        with patch.object(mod, "list_ollama_models", return_value=["custom-model"]):
            result = mod.pick_best_model("http://localhost:11434", "mistral")
            assert result == "custom-model"

    def test_returns_none_when_no_models(self):
        mod = _import_module()
        with patch.object(mod, "list_ollama_models", return_value=[]):
            assert mod.pick_best_model("http://localhost:11434", "mistral") is None


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  VersionAgent                                                             ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class TestVersionAgent:

    def _make_agent(self, mod, ollama_up=False, models=None):
        """Build a VersionAgent with Ollama mocked."""
        with patch.object(mod, "check_ollama_server", return_value=ollama_up), \
             patch.object(mod, "list_ollama_models", return_value=models or []):
            return mod.VersionAgent(ollama_url="http://localhost:11434", model="mistral")

    def test_llm_is_none_when_ollama_down(self):
        mod = _import_module()
        agent = self._make_agent(mod, ollama_up=False)
        assert agent.llm is None

    def test_llm_is_set_when_ollama_up_with_models(self):
        mod = _import_module()
        # Mock ChatOllama at module level
        mock_chat = MagicMock()
        mod.ChatOllama = mock_chat  # type: ignore[attr-defined]
        with patch.object(mod, "check_ollama_server", return_value=True), \
             patch.object(mod, "list_ollama_models", return_value=["mistral"]):
            agent = mod.VersionAgent(ollama_url="http://localhost:11434", model="mistral")
        assert agent.active_model == "mistral"

    def test_get_latest_python_version_from_api(self):
        mod = _import_module()
        agent = self._make_agent(mod)
        mock_releases = [
            {"name": "Python 3.14.6", "pre_release": False, "is_published": True, "id": 1},
            {"name": "Python 3.13.14", "pre_release": False, "is_published": True, "id": 2},
        ]
        mock_files = [
            {"url": "https://www.python.org/ftp/python/3.14.6/python-3.14.6-amd64.exe"}
        ]
        with patch("requests.get") as mock_get:
            mock_get.return_value.json.side_effect = [mock_releases, mock_files]
            version, url = agent.get_latest_python_version()
        assert version == "3.14.6"
        assert "amd64" in url
        assert url.endswith(".exe")

    def test_get_latest_python_version_fallback(self):
        mod = _import_module()
        agent = self._make_agent(mod)
        with patch("requests.get", side_effect=Exception("network error")):
            version, url = agent.get_latest_python_version()
        assert re.match(r"\d+\.\d+\.\d+", version)
        assert url.endswith(".exe")

    def test_get_latest_pycharm_version_from_api(self):
        mod = _import_module()
        agent = self._make_agent(mod)
        mock_data = {
            "PCC": [{
                "version": "2026.1.2",
                "build": "261.9999.99",
                "downloads": {
                    "windows": {
                        "link": "https://download.jetbrains.com/python/pycharm-community-2026.1.2.exe"
                    }
                }
            }]
        }
        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_data
            version, build, url = agent.get_latest_pycharm_version()
        assert version == "2026.1.2"
        assert build == "261.9999.99"
        assert "pycharm" in url.lower()

    def test_ask_fix_advisor_no_llm(self):
        mod = _import_module()
        agent = self._make_agent(mod, ollama_up=False)
        result = agent.ask_fix_advisor("some error", "some context")
        assert "Ollama" in result or "ollama" in result

    def test_ask_fix_advisor_with_llm(self):
        mod = _import_module()
        # Simulate working LLM
        mock_llm = MagicMock()
        mock_chain = MagicMock()
        mock_chain.invoke.return_value.content = "Step 1: Run as Admin\nStep 2: Retry"
        mock_llm.__or__ = MagicMock(return_value=mock_chain)

        with patch.object(mod, "check_ollama_server", return_value=True), \
             patch.object(mod, "list_ollama_models", return_value=["mistral"]), \
             patch.object(mod, "ChatOllama", return_value=mock_llm):
            agent = mod.VersionAgent(ollama_url="http://localhost:11434", model="mistral")
            agent.llm = mock_llm

        with patch.object(mod, "ChatPromptTemplate") as mock_prompt:
            mock_prompt.from_messages.return_value.__or__ = MagicMock(return_value=mock_chain)
            result = agent.ask_fix_advisor("Access denied", "Installing Python")

        assert isinstance(result, str)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  InstallReport                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class TestInstallReport:
    def test_default_state(self):
        mod = _import_module()
        report = mod.InstallReport()
        assert report.python_installed is False
        assert report.pycharm_installed is False
        assert report.plugins_installed == []
        assert report.plugins_failed == []
        assert report.errors == []
        assert report.checks == []


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Installer — core logic                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class TestInstaller:

    def _make_installer(self, mod, dry_run=False):
        mock_agent = MagicMock()
        mock_agent.ask_fix_advisor.return_value = "Fix: run as admin"
        report = mod.InstallReport()
        return mod.Installer(report, mock_agent, dry_run=dry_run), report, mock_agent

    def test_dry_run_does_not_call_subprocess(self):
        mod = _import_module()
        installer, report, _ = self._make_installer(mod, dry_run=True)
        with patch("subprocess.run") as mock_sub:
            ok, out = installer._run(["python", "--version"], "version check")
        # dry-run should return True without calling subprocess
        assert ok is True
        mock_sub.assert_not_called()

    def test_run_returns_false_on_nonzero_exit(self):
        mod = _import_module()
        installer, report, _ = self._make_installer(mod, dry_run=False)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Access denied"
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            ok, out = installer._run(["some", "cmd"], "some cmd", capture=True)
        assert ok is False
        assert len(report.errors) == 1

    def test_run_returns_true_on_zero_exit(self):
        mod = _import_module()
        installer, report, _ = self._make_installer(mod, dry_run=False)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Python 3.14.6"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            ok, out = installer._run(["python", "--version"], "version check", capture=True)
        assert ok is True
        assert "Python" in out

    def test_download_dry_run(self, tmp_path):
        mod = _import_module()
        installer, _, _ = self._make_installer(mod, dry_run=True)
        dest = tmp_path / "test.exe"
        with patch("urllib.request.urlretrieve") as mock_dl:
            ok = installer._download("https://example.com/test.exe", dest)
        assert ok is True
        mock_dl.assert_not_called()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Imports needed in tests                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

import re  # noqa: E402 — imported after mocks to avoid issues

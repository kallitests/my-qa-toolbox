"""
setup_dev_env.py
================
AI-powered installer — Python + PyCharm + plugins
Uses LangChain + un LLM au choix (local ou cloud gratuit) pour récupérer
les dernières versions, tout installer, lancer les health checks et proposer
des correctifs en cas d'erreur.

LLMs supportés (tous GRATUITS, sans frais de tokens) :
  1. Ollama          — local,  aucune clé API  (https://ollama.com)
  2. Google Gemini   — cloud ☁️, clé gratuite  (https://aistudio.google.com/apikey)
  3. Groq            — cloud ☁️, clé gratuite  (https://console.groq.com)
  4. Mistral AI      — cloud ☁️, clé gratuite  (https://console.mistral.ai)
  5. HuggingFace     — cloud ☁️, clé gratuite  (https://huggingface.co/settings/tokens)
  6. Cohere          — cloud ☁️, clé gratuite  (https://dashboard.cohere.com/api-keys)

Requirements (auto-installés) :
  pip install langchain langchain-ollama langchain-google-genai
              langchain-groq langchain-mistralai langchain-huggingface
              langchain-cohere requests rich

Usage :
  python setup_dev_env.py                          # menu interactif de choix du LLM
  python setup_dev_env.py --dry-run                # affiche le plan, n'installe rien
  python setup_dev_env.py --force                  # réinstalle même si déjà présent
  python setup_dev_env.py --llm ollama             # choisir le LLM via argument
  python setup_dev_env.py --llm groq --api-key ... # LLM cloud avec clé API
  python setup_dev_env.py --model llama3.2         # modèle Ollama spécifique
  python setup_dev_env.py --ollama-url http://...  # URL Ollama personnalisée
"""

# ── stdlib ──────────────────────────────────────────────────────────────────
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ── third-party (auto-installed below if missing) ───────────────────────────
def _bootstrap():
    """Install minimum dependencies before the main script runs."""
    needed = [
        "langchain", "langchain-ollama", "langchain-google-genai",
        "langchain-groq", "langchain-mistralai", "langchain-huggingface",
        "langchain-cohere", "requests", "rich", "python-dotenv",
    ]
    missing = []
    for pkg in needed:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[bootstrap] Installing: {', '.join(missing)}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        )

_bootstrap()

# Charge les variables du fichier .env situe dans le meme dossier que ce script.
# Cree un fichier .env avec : GROQ_API_KEY=gsk_xxxxxxxxxxxx
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

console = Console()

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  MENU SÉLECTION LLM                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

LLM_MENU = [
    {
        "key": "ollama",
        "label": "Ollama",
        "location": "LOCAL  (aucune clé API — tourne sur votre machine)",
        "free_tier": "∞ illimité",
        "url": "https://ollama.com/download",
        "default_model": "mistral",
        "env_key": None,
    },
    {
        "key": "gemini",
        "label": "Google Gemini",
        "location": "CLOUD ☁️ (clé gratuite — https://aistudio.google.com/apikey)",
        "free_tier": "15 req/min · 1 M tokens/jour",
        "url": "https://aistudio.google.com/apikey",
        "default_model": "gemini-1.5-flash",
        "env_key": "GEMINI_API_KEY",
    },
    {
        "key": "groq",
        "label": "Groq",
        "location": "CLOUD ☁️ (clé gratuite — https://console.groq.com)",
        "free_tier": "~14 400 req/jour (très rapide)",
        "url": "https://console.groq.com",
        "default_model": "llama3-8b-8192",
        "env_key": "GROQ_API_KEY",
    },
    {
        "key": "mistral",
        "label": "Mistral AI",
        "location": "CLOUD ☁️ (clé gratuite — https://console.mistral.ai)",
        "free_tier": "Free tier (rate-limited)",
        "url": "https://console.mistral.ai",
        "default_model": "mistral-small-latest",
        "env_key": "MISTRAL_API_KEY",
    },
    {
        "key": "huggingface",
        "label": "HuggingFace Inference API",
        "location": "CLOUD ☁️ (clé gratuite — https://huggingface.co/settings/tokens)",
        "free_tier": "~1 000 req/jour · centaines de modèles",
        "url": "https://huggingface.co/settings/tokens",
        "default_model": "mistralai/Mistral-7B-Instruct-v0.3",
        "env_key": "HUGGINGFACEHUB_API_TOKEN",
    },
    {
        "key": "cohere",
        "label": "Cohere",
        "location": "CLOUD ☁️ (clé gratuite — https://dashboard.cohere.com/api-keys)",
        "free_tier": "1 000 req/mois",
        "url": "https://dashboard.cohere.com/api-keys",
        "default_model": "command-r",
        "env_key": "COHERE_API_KEY",
    },
]


def show_llm_menu() -> dict:
    """Affiche le menu interactif de sélection du LLM. Retourne le choix."""
    console.print(Panel(
        "[bold white]Choix du LLM (tous gratuits, sans frais de tokens)[/bold white]",
        border_style="cyan",
    ))

    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    table.add_column("#",          style="bold yellow", justify="right", width=3)
    table.add_column("LLM",        style="bold white",  width=26)
    table.add_column("Localisation",                    width=58)
    table.add_column("Free tier",  style="green",       width=28)

    for i, entry in enumerate(LLM_MENU, 1):
        table.add_row(str(i), entry["label"], entry["location"], entry["free_tier"])

    console.print(table)
    console.print()

    while True:
        try:
            raw = input("  Entrez le numéro de votre choix [1-6] : ").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(LLM_MENU):
                return LLM_MENU[idx]
            console.print("[red]  ⚠ Numéro invalide. Choisissez entre 1 et 6.[/red]")
        except (ValueError, EOFError):
            console.print("[red]  ⚠ Entrée invalide.[/red]")


def get_api_key(entry: dict, cli_key: Optional[str]) -> Optional[str]:
    """
    Retourne la clé API pour un provider cloud.
    Ordre de priorité : argument CLI → variable d'environnement → saisie manuelle.
    Pour Ollama (local), retourne None directement.
    """
    if entry["env_key"] is None:
        return None  # Ollama — pas de clé nécessaire

    # 1. Clé passée en argument CLI
    if cli_key:
        return cli_key

    # 2. Variable d'environnement
    key = os.getenv(entry["env_key"], "")
    if key:
        console.print(
            f"[green]✅ Clé API trouvée dans la variable d'environnement "
            f"[bold]{entry['env_key']}[/bold][/green]"
        )
        return key

    # 3. Saisie manuelle
    console.print(
        f"\n[yellow]  Clé API requise pour [bold]{entry['label']}[/bold].[/yellow]"
    )
    console.print(
        f"  [dim]→ Obtenez-en une gratuitement : {entry['url']}[/dim]"
    )
    console.print(
        f"  [dim]→ Ou définissez la variable d'env : "
        f"[bold]{entry['env_key']}=votre_clé[/bold][/dim]\n"
    )
    try:
        key = input(f"  Collez votre clé API {entry['label']} : ").strip()
        return key if key else None
    except EOFError:
        return None


def build_llm(entry: dict, api_key: Optional[str], ollama_url: str, model_override: Optional[str]):
    """Instancie le LangChain LLM selon le provider choisi. Retourne (llm, model_name)."""
    model = model_override or entry["default_model"]

    if entry["key"] == "ollama":
        # Vérification Ollama
        if not check_ollama_server(ollama_url):
            console.print(
                f"[yellow]⚠ Ollama non joignable sur {ollama_url}[/yellow]\n"
                "[dim]  → Installez : https://ollama.com/download\n"
                "  → Démarrez  : ollama serve\n"
                "  → Tirez     : ollama pull mistral\n"
                "  Suggestions de fix IA désactivées pour cette session.[/dim]"
            )
            return None, None

        best = pick_best_model(ollama_url, model)
        if best is None:
            console.print(f"[yellow]⚠ Aucun modèle local trouvé. Tentative de pull '{model}'...[/yellow]")
            if pull_ollama_model(model, ollama_url):
                best = model
            else:
                console.print("[yellow]⚠ Pull échoué. Lancez : ollama pull mistral[/yellow]")
                return None, None
        if best != model:
            console.print(f"[yellow]⚠ Modèle '{model}' absent. Utilisation de '{best}'.[/yellow]")

        llm = ChatOllama(model=best, base_url=ollama_url, temperature=0.2, num_predict=512)
        return llm, best

    if not api_key:
        console.print(f"[red]❌ Clé API manquante pour {entry['label']}. IA désactivée.[/red]")
        return None, None

    try:
        if entry["key"] == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0.2)

        elif entry["key"] == "groq":
            from langchain_groq import ChatGroq
            llm = ChatGroq(model_name=model, groq_api_key=api_key, temperature=0.2)

        elif entry["key"] == "mistral":
            from langchain_mistralai import ChatMistralAI
            llm = ChatMistralAI(model=model, mistral_api_key=api_key, temperature=0.2)

        elif entry["key"] == "huggingface":
            from langchain_huggingface import HuggingFaceEndpoint
            llm = HuggingFaceEndpoint(
                repo_id=model,
                huggingfacehub_api_token=api_key,
                temperature=0.2,
                max_new_tokens=512,
            )

        elif entry["key"] == "cohere":
            from langchain_cohere import ChatCohere
            llm = ChatCohere(model=model, cohere_api_key=api_key, temperature=0.2)

        else:
            console.print(f"[red]❌ Provider inconnu : {entry['key']}[/red]")
            return None, None

        console.print(
            f"[green]✅ {entry['label']} prêt — modèle : [bold]{model}[/bold][/green]"
        )
        return llm, model

    except Exception as e:
        console.print(f"[red]❌ Initialisation {entry['label']} échouée : {e}[/red]")
        return None, None

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  CONFIGURATION                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # unused — kept for compatibility
OLLAMA_BASE_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL      = os.getenv("OLLAMA_MODEL", "mistral")   # change to llama3.2, codellama, etc.

# Models known to work well for fix suggestions (ordered by preference)
RECOMMENDED_MODELS = ["mistral", "llama3.2", "llama3", "codellama", "phi3", "gemma2"]

# PyCharm plugins to install (plugin IDs from JetBrains Marketplace)
PYCHARM_PLUGINS: list[dict] = [
    # ── Git & version control ────────────────────────────────────────────
    {"id": "Git4Idea",              "name": "Git",                         "category": "VCS"},
    {"id": "GitHub",                "name": "GitHub",                      "category": "VCS"},
    {"id": "org.zmlx.hg4idea",     "name": "Mercurial",                   "category": "VCS"},
    {"id": "Gitignore",             "name": ".ignore (gitignore)",         "category": "VCS"},
    {"id": "com.github.gitmachinelearning.gittoolbox", "name": "GitToolBox", "category": "VCS"},

    # ── AI & LLM ─────────────────────────────────────────────────────────
    {"id": "com.github.copilot",    "name": "GitHub Copilot",             "category": "AI"},
    {"id": "com.intellij.ml.llm",  "name": "AI Assistant (JetBrains)",   "category": "AI"},
    {"id": "com.github.cursor",     "name": "Cursor AI (if available)",   "category": "AI"},

    # ── Python & scripting ───────────────────────────────────────────────
    {"id": "PythonCore",            "name": "Python (core)",               "category": "Python"},
    {"id": "Pythonid",              "name": "Python Professional",         "category": "Python"},
    {"id": "com.jetbrains.python.envs", "name": "Python Envs",           "category": "Python"},
    {"id": "requirement",           "name": "Requirements",                "category": "Python"},
    {"id": "Toml",                  "name": "TOML",                        "category": "Python"},

    # ── LangChain / LangGraph / LangSmith ───────────────────────────────
    # No dedicated JetBrains plugins yet — covered via:
    # Python plugin + AI Assistant + Jupyter
    {"id": "org.jetbrains.plugins.jupyter", "name": "Jupyter",           "category": "LangChain"},
    {"id": "intellij.prettierJS",   "name": "Prettier (JSON/YAML)",       "category": "LangChain"},
    {"id": "com.intellij.swagger",  "name": "Swagger / OpenAPI",          "category": "LangChain"},

    # ── Docker & DevOps ──────────────────────────────────────────────────
    {"id": "Docker",                "name": "Docker",                      "category": "DevOps"},
    {"id": "net.seesharpsoft.intellij.plugins.csv", "name": "CSV Editor", "category": "DevOps"},
    {"id": "com.intellij.kubernetes", "name": "Kubernetes",               "category": "DevOps"},

    # ── Code quality ─────────────────────────────────────────────────────
    {"id": "CheckStyle-IDEA",       "name": "CheckStyle",                  "category": "Quality"},
    {"id": "SonarLint",             "name": "SonarLint",                   "category": "Quality"},
    {"id": "com.github.rjray.ideavim", "name": "IdeaVim (optional)",      "category": "Quality"},

    # ── Productivity ─────────────────────────────────────────────────────
    {"id": "com.intellij.ideolog",  "name": "ideolog (log viewer)",       "category": "Productivity"},
    {"id": "String Manipulation",   "name": "String Manipulation",         "category": "Productivity"},
    {"id": "com.intellij.rainbow.brackets", "name": "Rainbow Brackets",   "category": "Productivity"},
    {"id": "izhangzhihao.rainbow.brackets", "name": "Rainbow Brackets 2", "category": "Productivity"},
    {"id": "Markdown",              "name": "Markdown",                    "category": "Productivity"},
    {"id": "com.jetbrains.env",     "name": ".env files support",         "category": "Productivity"},
]

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  DATA MODELS                                                             ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@dataclass
class VersionInfo:
    python_latest: str = ""
    python_download_url: str = ""
    pycharm_latest: str = ""
    pycharm_download_url: str = ""
    pycharm_build: str = ""

@dataclass
class CheckResult:
    name: str
    status: str          # "ok" | "warning" | "error" | "skip"
    message: str
    fix: Optional[str] = None

@dataclass
class InstallReport:
    checks: list[CheckResult] = field(default_factory=list)
    python_installed: bool = False
    pycharm_installed: bool = False
    plugins_installed: list[str] = field(default_factory=list)
    plugins_failed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  OLLAMA HELPERS                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def check_ollama_server(base_url: str) -> bool:
    """Ping Ollama server. Returns True if reachable."""
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False

def list_ollama_models(base_url: str) -> list[str]:
    """Return list of locally pulled model names."""
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        data = resp.json()
        return [m["name"].split(":")[0] for m in data.get("models", [])]
    except Exception:
        return []

def pick_best_model(base_url: str, preferred: str) -> Optional[str]:
    """
    Return the best available model:
    1. The user's preferred model if pulled
    2. First match in RECOMMENDED_MODELS
    3. Any available model
    4. None if Ollama is unreachable / empty
    """
    available = list_ollama_models(base_url)
    if not available:
        return None
    if preferred in available:
        return preferred
    for m in RECOMMENDED_MODELS:
        if m in available:
            return m
    return available[0]

def pull_ollama_model(model: str, base_url: str) -> bool:
    """Pull a model via Ollama REST API (streaming)."""
    console.print(f"[cyan]⬇ Pulling Ollama model '{model}' (this may take a few minutes)...[/cyan]")
    try:
        with requests.post(
            f"{base_url}/api/pull",
            json={"name": model, "stream": False},
            timeout=600,
        ) as resp:
            return resp.status_code == 200
    except Exception as e:
        console.print(f"[red]❌ Pull failed: {e}[/red]")
        return False

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  LANGCHAIN AGENT — version fetcher + fix advisor (multi-LLM)             ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class VersionAgent:
    """Uses LangChain + the chosen LLM to provide fix suggestions."""

    def __init__(self, llm, active_model: Optional[str], provider_label: str):
        self.llm = llm
        self.active_model = active_model
        self.provider_label = provider_label

    def get_latest_python_version(self) -> tuple[str, str]:
        """Returns (version_string, download_url_windows_64bit)."""
        console.print("[cyan]🔍 Fetching latest Python version...[/cyan]")

        # Primary: python.org JSON API (no LLM needed — pure HTTP)
        try:
            resp = requests.get(
                "https://www.python.org/api/v2/downloads/release/"
                "?is_published=true&pre_release=false",
                timeout=10,
            )
            releases = resp.json()
            stable = [
                r for r in releases
                if not r.get("pre_release") and r.get("is_published") is not False
            ]
            latest = sorted(
                stable,
                key=lambda r: [int(x) for x in re.findall(r"\d+", r["name"])],
                reverse=True,
            )[0]
            version = re.search(r"(\d+\.\d+\.\d+)", latest["name"]).group(1)

            files_resp = requests.get(
                f"https://www.python.org/api/v2/downloads/release_file/"
                f"?release={latest['id']}",
                timeout=10,
            )
            files = files_resp.json()
            win64 = next(
                (f["url"] for f in files
                 if "amd64" in f["url"] and f["url"].endswith(".exe")),
                f"https://www.python.org/ftp/python/{version}/python-{version}-amd64.exe",
            )
            console.print(f"[green]✅ Python latest: {version}[/green]")
            return version, win64

        except Exception as e:
            console.print(f"[yellow]⚠ python.org API error: {e} — using known fallback[/yellow]")
            version = "3.14.6"
            return version, f"https://www.python.org/ftp/python/{version}/python-{version}-amd64.exe"

    def get_latest_pycharm_version(self) -> tuple[str, str, str]:
        """Returns (version_string, build_number, download_url)."""
        console.print("[cyan]🔍 Fetching latest PyCharm version...[/cyan]")

        try:
            resp = requests.get(
                "https://data.services.jetbrains.com/products/releases"
                "?code=PCC&latest=true&type=release",
                timeout=10,
            )
            data = resp.json()
            release = data["PCC"][0]
            version = release["version"]
            build   = release["build"]
            url     = release["downloads"]["windows"]["link"]
            console.print(f"[green]✅ PyCharm Community latest: {version} (build {build})[/green]")
            return version, build, url

        except Exception as e:
            console.print(f"[yellow]⚠ JetBrains API error: {e} — using known fallback[/yellow]")
            version = "2026.1.2"
            build   = "261.9999.99"
            url     = f"https://download.jetbrains.com/python/pycharm-community-{version}.exe"
            return version, build, url

    def ask_fix_advisor(self, error: str, context: str) -> str:
        """
        Ask the chosen LLM for a fix suggestion.
        Falls back to a static hint if the LLM is unavailable.
        """
        if not self.llm:
            return (
                "💡 Aucun LLM disponible — suggestions de fix désactivées.\n"
                "   Relancez le script et choisissez un LLM valide.\n"
                f"   Erreur : {error[:200]}"
            )

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                "You are a Windows developer environment expert. "
                "When given an error during Python or PyCharm installation on Windows, "
                "provide a concise, actionable fix in 3 numbered steps maximum. "
                "Be specific to Windows PowerShell and Git Bash commands. "
                "Keep your answer under 150 words. "
                "Reply in the same language as the error message."
            )),
            HumanMessage(content=(
                f"Context: {context}\n\n"
                f"Error:\n{error[:500]}"
            )),
        ])
        chain = prompt | self.llm

        try:
            console.print(
                f"[dim]  🤖 Asking {self.provider_label} ({self.active_model}) for a fix...[/dim]"
            )
            result = chain.invoke({})
            return result.content if hasattr(result, "content") else str(result)
        except Exception as e:
            return (
                f"Requête LLM échouée ({e}).\n"
                "Correctifs courants :\n"
                "  1. Lancez PowerShell en tant qu'Administrateur\n"
                "  2. Set-ExecutionPolicy RemoteSigned -Scope CurrentUser\n"
                "  3. Redémarrez le terminal après l'installation"
            )

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SYSTEM CHECKS                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class SystemChecker:

    def __init__(self, report: InstallReport, ollama_url: str = OLLAMA_BASE_URL):
        self.report = report
        self.ollama_url = ollama_url

    def _add(self, name: str, status: str, message: str, fix: str = None):
        r = CheckResult(name=name, status=status, message=message, fix=fix)
        self.report.checks.append(r)
        icon = {"ok": "✅", "warning": "⚠️ ", "error": "❌", "skip": "⏭️ "}[status]
        color = {"ok": "green", "warning": "yellow", "error": "red", "skip": "dim"}[status]
        console.print(f"  [{color}]{icon} {name}: {message}[/{color}]")
        if fix:
            console.print(f"     [dim]→ Fix: {fix}[/dim]")

    def check_os(self):
        os_name = platform.system()
        version = platform.version()
        arch = platform.machine()
        if os_name == "Windows":
            self._add("OS", "ok", f"Windows {version} ({arch})")
        else:
            self._add("OS", "warning",
                f"{os_name} detected — this script targets Windows. Some steps may differ.",
                fix="Run on Windows 10/11 for full compatibility.")

    def check_admin(self):
        """Check if running as administrator."""
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                self._add("Admin rights", "ok", "Running as Administrator")
            else:
                self._add("Admin rights", "warning",
                    "Not running as Administrator — some installs may fail.",
                    fix="Right-click PowerShell → 'Run as Administrator', then re-run this script.")
        except Exception:
            self._add("Admin rights", "skip", "Cannot determine (non-Windows)")

    def check_execution_policy(self):
        """Check PowerShell execution policy."""
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-ExecutionPolicy"],
                capture_output=True, text=True, timeout=10,
            )
            policy = result.stdout.strip()
            if policy in ("RemoteSigned", "Unrestricted", "Bypass"):
                self._add("PS ExecutionPolicy", "ok", f"Policy: {policy}")
            else:
                self._add("PS ExecutionPolicy", "error",
                    f"Policy '{policy}' blocks .ps1 scripts (venv activation will fail).",
                    fix="Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser")
        except Exception as e:
            self._add("PS ExecutionPolicy", "skip", f"Cannot check: {e}")

    def check_winget(self):
        """Check if winget is available."""
        if shutil.which("winget"):
            result = subprocess.run(["winget", "--version"], capture_output=True, text=True)
            self._add("winget", "ok", f"Available — {result.stdout.strip()}")
            return True
        else:
            self._add("winget", "warning",
                "winget not found — will use direct download instead.",
                fix="Install App Installer from Microsoft Store to get winget.")
            return False

    def check_existing_python(self) -> Optional[str]:
        """Returns existing Python version string or None."""
        py = shutil.which("python") or shutil.which("python3")
        if py:
            result = subprocess.run([py, "--version"], capture_output=True, text=True)
            version = result.stdout.strip() or result.stderr.strip()
            self._add("Python (existing)", "ok", f"{version} at {py}")
            return version
        else:
            self._add("Python (existing)", "warning", "No Python found in PATH")
            return None

    def check_existing_pycharm(self) -> Optional[Path]:
        """Returns PyCharm install path or None."""
        common = [
            Path("C:/Program Files/JetBrains"),
            Path("C:/Program Files (x86)/JetBrains"),
            Path(os.path.expanduser("~")) / "AppData/Local/JetBrains",
        ]
        for base in common:
            if base.exists():
                matches = list(base.glob("PyCharm*"))
                if matches:
                    path = matches[-1]
                    self._add("PyCharm (existing)", "ok", f"Found at {path}")
                    return path
        self._add("PyCharm (existing)", "warning", "No PyCharm installation found")
        return None

    def check_disk_space(self):
        """Check available disk space (need ~2 GB for Python + PyCharm)."""
        try:
            usage = shutil.disk_usage("C:/")
            free_gb = usage.free / (1024 ** 3)
            if free_gb >= 3:
                self._add("Disk space", "ok", f"{free_gb:.1f} GB free on C:")
            elif free_gb >= 1.5:
                self._add("Disk space", "warning",
                    f"Only {free_gb:.1f} GB free — tight but might work.",
                    fix="Free up space on C: before installing.")
            else:
                self._add("Disk space", "error",
                    f"Only {free_gb:.1f} GB free — not enough for installation.",
                    fix="Free at least 3 GB on C: before running this script.")
        except Exception as e:
            self._add("Disk space", "skip", f"Cannot check: {e}")

    def check_internet(self):
        """Check internet connectivity."""
        try:
            urllib.request.urlopen("https://www.python.org", timeout=5)
            self._add("Internet", "ok", "python.org reachable")
        except Exception:
            try:
                urllib.request.urlopen("https://8.8.8.8", timeout=5)
                self._add("Internet", "warning",
                    "python.org unreachable but internet seems up — check firewall/proxy.",
                    fix="Check corporate proxy settings. Set HTTP_PROXY/HTTPS_PROXY env vars if needed.")
            except Exception:
                self._add("Internet", "error",
                    "No internet connection detected.",
                    fix="Connect to internet and re-run the script.")

    def check_pip(self):
        """Check pip availability."""
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            self._add("pip", "ok", result.stdout.strip())
        else:
            self._add("pip", "error",
                "pip not available.",
                fix="Run: python -m ensurepip --upgrade")

    def check_ollama(self):
        """Check Ollama server and available models."""
        if not check_ollama_server(self.ollama_url):
            self._add(
                "Ollama server", "warning",
                f"Not reachable at {self.ollama_url} — AI fix suggestions disabled.",
                fix=(
                    "1. Install Ollama: https://ollama.com/download\n"
                    "     2. Start server: ollama serve\n"
                    "     3. Pull a model: ollama pull mistral"
                ),
            )
            return

        models = list_ollama_models(self.ollama_url)
        if not models:
            self._add(
                "Ollama models", "warning",
                "Ollama is running but no models are pulled yet.",
                fix="Run: ollama pull mistral   (or llama3.2, codellama, phi3...)",
            )
        else:
            best = pick_best_model(self.ollama_url, OLLAMA_MODEL)
            self._add(
                "Ollama models", "ok",
                f"{len(models)} model(s) available — will use: [bold]{best}[/bold]  "
                f"(all: {', '.join(models)})",
            )

    def run_all(self) -> bool:
        """Run all checks. Returns False if any critical error found."""
        console.print("\n[bold cyan]── System checks ──────────────────────────────[/bold cyan]")
        self.check_os()
        self.check_admin()
        self.check_execution_policy()
        self.check_winget()
        self.check_existing_python()
        self.check_existing_pycharm()
        self.check_disk_space()
        self.check_internet()
        self.check_pip()
        self.check_ollama()   # ← Ollama check added

        errors = [c for c in self.report.checks if c.status == "error"]
        if errors:
            console.print(f"\n[red]❌ {len(errors)} critical error(s) found — fix them before proceeding.[/red]")
            return False
        return True

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  INSTALLER                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class Installer:

    def __init__(self, report: InstallReport, agent: VersionAgent, dry_run: bool = False):
        self.report = report
        self.agent = agent
        self.dry_run = dry_run
        self.tmp = Path(tempfile.gettempdir()) / "setup_dev_env"
        self.tmp.mkdir(exist_ok=True)

    def _download(self, url: str, dest: Path) -> bool:
        """Download a file with progress bar."""
        console.print(f"[cyan]⬇ Downloading {dest.name}...[/cyan]")
        if self.dry_run:
            console.print(f"  [dim][DRY-RUN] Would download: {url}[/dim]")
            return True
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Downloading {dest.name}", total=None)
                urllib.request.urlretrieve(url, dest)
                progress.update(task, completed=True)
            console.print(f"[green]✅ Downloaded to {dest}[/green]")
            return True
        except Exception as e:
            error_msg = str(e)
            console.print(f"[red]❌ Download failed: {error_msg}[/red]")
            fix = self.agent.ask_fix_advisor(error_msg, f"Downloading {url}")
            console.print(Panel(fix, title="🤖 AI Fix Suggestion", border_style="yellow"))
            self.report.errors.append(f"Download {dest.name}: {error_msg}")
            return False

    def _run(self, cmd: list[str], desc: str, capture: bool = False) -> tuple[bool, str]:
        """Run a subprocess with error handling."""
        if self.dry_run:
            console.print(f"  [dim][DRY-RUN] Would run: {' '.join(cmd)}[/dim]")
            return True, ""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture,
                text=True,
                timeout=600,  # 10 min max per command
            )
            if result.returncode != 0:
                error = result.stderr or result.stdout or f"Exit code {result.returncode}"
                console.print(f"[red]❌ {desc} failed: {error[:300]}[/red]")
                fix = self.agent.ask_fix_advisor(error, desc)
                console.print(Panel(fix, title="🤖 AI Fix Suggestion", border_style="yellow"))
                self.report.errors.append(f"{desc}: {error[:200]}")
                return False, error
            return True, result.stdout or ""
        except subprocess.TimeoutExpired:
            msg = f"{desc} timed out after 10 minutes"
            console.print(f"[red]❌ {msg}[/red]")
            self.report.errors.append(msg)
            return False, msg
        except Exception as e:
            msg = str(e)
            console.print(f"[red]❌ {desc} exception: {msg}[/red]")
            fix = self.agent.ask_fix_advisor(msg, desc)
            console.print(Panel(fix, title="🤖 AI Fix Suggestion", border_style="yellow"))
            self.report.errors.append(f"{desc}: {msg}")
            return False, msg

    # ── Python ─────────────────────────────────────────────────────────────

    def install_python(self, version: str, url: str, force: bool = False) -> bool:
        console.print(f"\n[bold cyan]── Installing Python {version} ──────────────────[/bold cyan]")

        # Check if already installed
        existing = subprocess.run(
            ["python", "--version"], capture_output=True, text=True
        )
        existing_ver = re.search(r"(\d+\.\d+\.\d+)", existing.stdout + existing.stderr)
        if existing_ver and existing_ver.group(1) == version and not force:
            console.print(f"[green]✅ Python {version} already installed — skipping.[/green]")
            self.report.python_installed = True
            return True

        # Try winget first
        console.print(f"[cyan]Trying winget install Python {version}...[/cyan]")
        major_minor = ".".join(version.split(".")[:2])  # e.g. "3.14"
        ok, out = self._run(
            ["winget", "install", "--id", f"Python.Python.{major_minor}",
             "--silent", "--accept-package-agreements", "--accept-source-agreements"],
            f"winget install Python {version}",
            capture=True,
        )

        if ok:
            console.print(f"[green]✅ Python {version} installed via winget.[/green]")
            self.report.python_installed = True
            return True

        # Fallback: direct installer download
        console.print("[yellow]⚠ winget failed — falling back to direct download...[/yellow]")
        installer = self.tmp / f"python-{version}-amd64.exe"
        if not self._download(url, installer):
            return False

        ok, _ = self._run(
            [str(installer),
             "/quiet",
             "InstallAllUsers=1",
             "PrependPath=1",
             "Include_test=0",
             "Include_doc=0",
             "Include_launcher=1",
             "AssociateFiles=1"],
            f"Python {version} silent install",
        )

        if ok:
            console.print(f"[green]✅ Python {version} installed.[/green]")
            self.report.python_installed = True
            # Refresh PATH
            time.sleep(2)
            self._verify_python(version)
        return ok

    def _verify_python(self, expected_version: str):
        console.print(f"\n[cyan]🔍 Verifying Python {expected_version}...[/cyan]")
        checks = [
            (["python", "--version"],     "python"),
            (["python3", "--version"],    "python3"),
            (["py", f"-{expected_version[:4]}", "--version"], "py launcher"),
        ]
        for cmd, label in checks:
            result = subprocess.run(cmd, capture_output=True, text=True)
            ver = re.search(r"(\d+\.\d+\.\d+)", result.stdout + result.stderr)
            if ver:
                console.print(f"  [green]✅ {label}: Python {ver.group(1)}[/green]")
                if ver.group(1) != expected_version:
                    console.print(f"  [yellow]⚠ Expected {expected_version}, got {ver.group(1)}.[/yellow]")
                    console.print("  [dim]→ PATH may still point to old version. Restart terminal.[/dim]")
                return
        console.print(f"[red]❌ Python not found in PATH after install.[/red]")
        console.print("[dim]→ Restart your terminal / PowerShell, then run: python --version[/dim]")

    # ── PyCharm ────────────────────────────────────────────────────────────

    def install_pycharm(self, version: str, build: str, url: str, force: bool = False) -> Optional[Path]:
        console.print(f"\n[bold cyan]── Installing PyCharm Community {version} ──────[/bold cyan]")

        # Check existing
        common_paths = [
            Path("C:/Program Files/JetBrains") / f"PyCharm Community Edition {version}",
            Path("C:/Program Files/JetBrains") / "PyCharm Community Edition",
        ]
        for p in common_paths:
            if p.exists() and not force:
                console.print(f"[green]✅ PyCharm {version} already installed at {p}[/green]")
                self.report.pycharm_installed = True
                return p

        # Try winget
        console.print("[cyan]Trying winget install PyCharm Community...[/cyan]")
        ok, _ = self._run(
            ["winget", "install", "--id", "JetBrains.PyCharm.Community",
             "--silent", "--accept-package-agreements", "--accept-source-agreements"],
            f"winget install PyCharm Community {version}",
            capture=True,
        )
        if ok:
            console.print(f"[green]✅ PyCharm {version} installed via winget.[/green]")
            self.report.pycharm_installed = True
            install_path = Path("C:/Program Files/JetBrains/PyCharm Community Edition")
            return install_path if install_path.exists() else None

        # Fallback: direct download
        console.print("[yellow]⚠ winget failed — falling back to direct download...[/yellow]")
        installer = self.tmp / f"pycharm-community-{version}.exe"
        if not self._download(url, installer):
            return None

        ok, _ = self._run(
            [str(installer),
             "/S",                          # silent
             "/D=C:\\Program Files\\JetBrains\\PyCharm Community Edition"],
            f"PyCharm {version} silent install",
        )

        if ok:
            console.print(f"[green]✅ PyCharm {version} installed.[/green]")
            self.report.pycharm_installed = True
            return Path("C:/Program Files/JetBrains/PyCharm Community Edition")

        return None

    # ── PyCharm plugins ────────────────────────────────────────────────────

    def _find_pycharm_script(self) -> Optional[Path]:
        """Find pycharm.bat or pycharm64.exe for CLI plugin install."""
        candidates = [
            Path("C:/Program Files/JetBrains/PyCharm Community Edition/bin/pycharm64.exe"),
            Path("C:/Program Files/JetBrains/PyCharm Community Edition/bin/pycharm.bat"),
            Path("C:/Program Files (x86)/JetBrains/PyCharm Community Edition/bin/pycharm64.exe"),
        ]
        # Also check JETBRAINS_TOOLBOX installations
        toolbox_base = Path(os.path.expanduser("~")) / "AppData/Local/JetBrains/Toolbox/apps/PyCharm-C"
        if toolbox_base.exists():
            for p in sorted(toolbox_base.rglob("pycharm64.exe"), reverse=True):
                candidates.insert(0, p)

        for c in candidates:
            if c.exists():
                return c
        return None

    def install_plugins(self, pycharm_build: str):
        """Install PyCharm plugins via the JetBrains plugin installer CLI."""
        console.print(f"\n[bold cyan]── Installing PyCharm plugins ─────────────────[/bold cyan]")

        pycharm_exe = self._find_pycharm_script()
        if not pycharm_exe:
            console.print("[yellow]⚠ PyCharm executable not found — cannot auto-install plugins.[/yellow]")
            console.print("[dim]→ Open PyCharm → Settings → Plugins and install manually:[/dim]")
            self._print_manual_plugin_list()
            return

        # Group plugins by category for display
        categories: dict[str, list] = {}
        for plugin in PYCHARM_PLUGINS:
            cat = plugin["category"]
            categories.setdefault(cat, []).append(plugin)

        for category, plugins in categories.items():
            console.print(f"\n  [bold]{category}[/bold]")
            for plugin in plugins:
                plugin_id = plugin["id"]
                name = plugin["name"]

                if self.dry_run:
                    console.print(f"  [dim][DRY-RUN] Would install plugin: {name} ({plugin_id})[/dim]")
                    self.report.plugins_installed.append(name)
                    continue

                # JetBrains CLI: pycharm64.exe installPlugins <pluginId>
                ok, out = self._run(
                    [str(pycharm_exe), "installPlugins", plugin_id],
                    f"Plugin: {name}",
                    capture=True,
                )
                if ok:
                    console.print(f"  [green]✅ {name}[/green]")
                    self.report.plugins_installed.append(name)
                else:
                    console.print(f"  [yellow]⚠ {name} — install via UI (Settings → Plugins → search '{name}')[/yellow]")
                    self.report.plugins_failed.append(name)

    def _print_manual_plugin_list(self):
        """Print a table of plugins to install manually."""
        table = Table(title="Plugins to install manually in PyCharm", show_lines=True)
        table.add_column("Category", style="cyan")
        table.add_column("Plugin name", style="white")
        table.add_column("Plugin ID", style="dim")

        for plugin in PYCHARM_PLUGINS:
            table.add_row(plugin["category"], plugin["name"], plugin["id"])

        console.print(table)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  POST-INSTALL CHECKS                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class PostInstallChecker:

    def __init__(self, report: InstallReport):
        self.report = report

    def verify_python_modules(self):
        """Verify that key modules work after install."""
        console.print("\n[bold cyan]── Post-install Python checks ─────────────────[/bold cyan]")
        modules = ["pip", "venv", "asyncio", "json", "pathlib", "urllib"]
        for mod in modules:
            result = subprocess.run(
                ["python", "-c", f"import {mod}; print('ok')"],
                capture_output=True, text=True,
            )
            if "ok" in result.stdout:
                console.print(f"  [green]✅ import {mod}[/green]")
            else:
                console.print(f"  [red]❌ import {mod} failed[/red]")
                self.report.errors.append(f"Python module {mod} not importable")

    def verify_venv_creation(self):
        """Test that venv creation works (the bug you hit earlier)."""
        console.print("\n[cyan]🔍 Testing venv creation...[/cyan]")
        test_dir = Path(tempfile.gettempdir()) / "test_venv_smokesentinel"
        try:
            if test_dir.exists():
                shutil.rmtree(test_dir)
            result = subprocess.run(
                ["python", "-m", "venv", str(test_dir)],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0 and (test_dir / "Scripts" / "python.exe").exists():
                console.print("  [green]✅ venv creation works correctly[/green]")
            else:
                error = result.stderr or result.stdout
                console.print(f"  [red]❌ venv creation failed: {error[:200]}[/red]")
                console.print("  [dim]→ Fix: Run PowerShell as Admin, or use: python -m venv .venv --without-pip[/dim]")
                self.report.errors.append(f"venv creation failed: {error[:100]}")
        except Exception as e:
            console.print(f"  [red]❌ venv test exception: {e}[/red]")
        finally:
            if test_dir.exists():
                shutil.rmtree(test_dir, ignore_errors=True)

    def run_all(self):
        self.verify_python_modules()
        self.verify_venv_creation()

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  FINAL REPORT                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def print_final_report(report: InstallReport, versions: VersionInfo):
    console.print("\n")
    console.rule("[bold white]Installation Report[/bold white]")

    # Summary table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Detail")

    table.add_row(
        f"Python {versions.python_latest}",
        "✅" if report.python_installed else "❌",
        "Installed and verified" if report.python_installed else "Installation failed",
    )
    table.add_row(
        f"PyCharm {versions.pycharm_latest}",
        "✅" if report.pycharm_installed else "❌",
        "Installed" if report.pycharm_installed else "Installation failed",
    )
    table.add_row(
        "PyCharm plugins",
        f"✅ {len(report.plugins_installed)}" if report.plugins_installed else "⚠️",
        f"{len(report.plugins_installed)} installed, {len(report.plugins_failed)} to install manually",
    )
    console.print(table)

    # Errors
    if report.errors:
        console.print(f"\n[red]── {len(report.errors)} error(s) to resolve ──[/red]")
        for i, err in enumerate(report.errors, 1):
            console.print(f"  [red]{i}. {err}[/red]")

    # Plugins to install manually
    if report.plugins_failed:
        console.print("\n[yellow]── Plugins to install manually in PyCharm ──[/yellow]")
        console.print("[dim]Settings → Plugins → Marketplace → search:[/dim]")
        for p in report.plugins_failed:
            console.print(f"  • {p}")

    # Next steps
    console.print(Panel(
        f"""[bold]Next steps for SmokeSentinel:[/bold]

1. Restart your terminal (PATH refresh after Python install)
2. Verify:  [cyan]python --version[/cyan]  →  Python {versions.python_latest}
3. Create venv:
   [cyan]cd C:\\kallitests\\smoke-tests-sentinel[/cyan]
   [cyan]python -m venv .venv[/cyan]
   [cyan].venv\\Scripts\\Activate.ps1[/cyan]    [dim](PowerShell)[/dim]
   [cyan]source .venv/Scripts/activate[/cyan]  [dim](Git Bash)[/dim]

4. Install SmokeSentinel dependencies:
   [cyan]pip install -e ".[dev]"[/cyan]

5. Open PyCharm → File → Open → C:\\kallitests\\smoke-tests-sentinel
   PyCharm will detect the venv automatically.

6. In PyCharm: Settings → Plugins → install any remaining plugins from the list above.

7. [bold]Ollama (local AI — already running if you used this script):[/bold]
   [cyan]ollama serve[/cyan]           [dim]# keep running in background[/dim]
   [cyan]ollama pull mistral[/cyan]    [dim]# or: llama3.2, codellama, phi3[/dim]
   [cyan]ollama list[/cyan]            [dim]# verify pulled models[/dim]
""",
        title="✅ Setup complete — next steps",
        border_style="green",
    ))

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  MAIN                                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def main():
    parser = argparse.ArgumentParser(
        description="AI-powered Python + PyCharm installer (multi-LLM, tous gratuits)"
    )
    parser.add_argument("--dry-run",      action="store_true", help="Affiche le plan sans installer")
    parser.add_argument("--force",        action="store_true", help="Réinstalle même si déjà présent")
    parser.add_argument("--skip-python",  action="store_true")
    parser.add_argument("--skip-pycharm", action="store_true")
    parser.add_argument("--skip-plugins", action="store_true")
    parser.add_argument(
        "--llm",
        choices=[e["key"] for e in LLM_MENU],
        default=None,
        help="LLM à utiliser : ollama | gemini | groq | mistral | huggingface | cohere",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Clé API du provider cloud (sinon saisie interactive ou variable d'env)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Modèle à utiliser (optionnel, remplace le modèle par défaut du provider)",
    )
    parser.add_argument(
        "--ollama-url",
        default=OLLAMA_BASE_URL,
        help=f"URL du serveur Ollama (défaut : {OLLAMA_BASE_URL})",
    )
    args = parser.parse_args()

    console.print(Panel(
        "[bold white]setup_dev_env.py[/bold white]\n"
        "AI-powered installer — Python + PyCharm + plugins\n"
        "[dim]LLMs supportés : Ollama (local) · Gemini · Groq · Mistral · HuggingFace · Cohere[/dim]\n"
        f"[dim]Plateforme     : {platform.system()} {platform.version()}[/dim]",
        border_style="cyan",
    ))

    if args.dry_run:
        console.print("[yellow]🔍 Mode DRY-RUN — rien ne sera installé.[/yellow]\n")

    # ── Sélection du LLM ──────────────────────────────────────────────────
    if args.llm:
        # Choix via argument CLI
        entry = next(e for e in LLM_MENU if e["key"] == args.llm)
        console.print(
            f"[cyan]🤖 LLM sélectionné via argument : [bold]{entry['label']}[/bold][/cyan]"
        )
    else:
        # Menu interactif
        entry = show_llm_menu()
        console.print(
            f"\n[cyan]🤖 LLM choisi : [bold]{entry['label']}[/bold] — {entry['location']}[/cyan]\n"
        )

    api_key = get_api_key(entry, args.api_key)
    llm, active_model = build_llm(entry, api_key, args.ollama_url, args.model)
    agent = VersionAgent(llm=llm, active_model=active_model, provider_label=entry["label"])

    # ── 1. System checks ───────────────────────────────────────────────────
    checker = SystemChecker(report := InstallReport(), ollama_url=args.ollama_url)
    checks_ok = checker.run_all()
    if not checks_ok:
        console.print("\n[red]Corrigez les erreurs ci-dessus avant de continuer.[/red]")
        sys.exit(1)

    # ── 2. Fetch latest versions ───────────────────────────────────────────
    console.print("\n[bold cyan]── Récupération des dernières versions ─────────[/bold cyan]")
    versions = VersionInfo()
    versions.python_latest, versions.python_download_url = agent.get_latest_python_version()
    versions.pycharm_latest, versions.pycharm_build, versions.pycharm_download_url = \
        agent.get_latest_pycharm_version()

    console.print(f"\n  Python  → [bold green]{versions.python_latest}[/bold green]")
    console.print(f"  PyCharm → [bold green]{versions.pycharm_latest}[/bold green] (build {versions.pycharm_build})")

    # ── 3. Install ─────────────────────────────────────────────────────────
    installer = Installer(report, agent, dry_run=args.dry_run)

    if not args.skip_python:
        installer.install_python(versions.python_latest, versions.python_download_url, args.force)

    if not args.skip_pycharm:
        installer.install_pycharm(
            versions.pycharm_latest,
            versions.pycharm_build,
            versions.pycharm_download_url,
            args.force,
        )

    if not args.skip_plugins:
        installer.install_plugins(versions.pycharm_build)

    # ── 4. Post-install checks ─────────────────────────────────────────────
    if not args.dry_run:
        post = PostInstallChecker(report)
        post.run_all()

    # ── 5. Final report ────────────────────────────────────────────────────
    print_final_report(report, versions)


if __name__ == "__main__":
    main()

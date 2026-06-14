"""Runtime configuration. Demo mode is auto-detected: if no LLM key is
present, the system runs entirely on the deterministic rule engine plus
cached reasoning, so a live demo never depends on network or API keys."""
import os
import logging
from pathlib import Path

os.environ["ANONYMIZED_TELEMETRY"] = "False"
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)



BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file manually if it exists to ensure proper environment connectivity
env_path = BASE_DIR / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        # setdefault allows overriding via system variables if already set
        os.environ[k.strip()] = v.strip().strip('"').strip("'")

POLICIES_DIR = BASE_DIR / "policies"
DEMO_DOCS_DIR = BASE_DIR / "demo_docs"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CHROMA_DIR = str(DATA_DIR / "chroma")
DB_PATH = str(DATA_DIR / "audit.sqlite")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# Demo mode = no real LLM available. Everything still works deterministically.
DEMO_MODE = not (OPENAI_API_KEY or AZURE_OPENAI_KEY or GROQ_API_KEY)

TRIAGE_MODEL = os.getenv("TRIAGE_MODEL", "gpt-4o-mini")
ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL", "gpt-4o")

# RAG grounding threshold: the LLM may not make a compliance call unless a
# policy chunk is retrieved above this cosine similarity.
GROUNDING_THRESHOLD = float(os.getenv("GROUNDING_THRESHOLD", "0.35"))

DEFAULT_TENANT = "acmecorp"

REGULATION_PRECEDENCE = {
    "gdpr": 1,              # highest
    "iso27001": 2,
    "sox": 3,
    "internal_security": 4,
    "internal_hr": 5,       # lowest
}
print("OPENAI:", bool(OPENAI_API_KEY))
print("GROQ:", bool(GROQ_API_KEY))
print("TRIAGE_MODEL:", TRIAGE_MODEL)
print("ANALYSIS_MODEL:", ANALYSIS_MODEL)
print("DEMO_MODE:", DEMO_MODE)
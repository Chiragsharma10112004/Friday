from dotenv import load_dotenv
import os

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "FRIDAY")
VERSION = os.getenv("VERSION", "0.1.0")
ENV = os.getenv("ENV", "development")

# AI Provider Routing
DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "ollama").lower().strip()
JOB_ANALYSIS_PROVIDER = os.getenv("JOB_ANALYSIS_PROVIDER", "").lower().strip() or DEFAULT_AI_PROVIDER

# Ollama Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

# OpenAI Configuration (Optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

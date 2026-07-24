import os
from pathlib import Path
from pydantic import BaseModel

CONFIG_DIR = Path.home() / ".config" / "faresta"
CONFIG_FILE = CONFIG_DIR / "config.yml"
HISTORY_DIR = CONFIG_DIR / "history"

PROVIDER_DEFAULTS = {
    "openai": {"model": "gpt-4o", "env_key": "OPENAI_API_KEY"},
    "anthropic": {"model": "claude-sonnet-4-20250514", "env_key": "ANTHROPIC_API_KEY"},
    "google": {"model": "gemini-2.5-flash", "env_key": "GOOGLE_API_KEY"},
    "groq": {"model": "llama-3.3-70b-versatile", "env_key": "GROQ_API_KEY"},
    "xai": {"model": "grok-2-1212", "env_key": "XAI_API_KEY"},
    "nvidia": {"model": "meta/llama-3.1-70b-instruct", "env_key": "NVIDIA_API_KEY"},
    "deepseek": {"model": "deepseek-chat", "env_key": "DEEPSEEK_API_KEY"},
    "mistral": {"model": "mistral-large-latest", "env_key": "MISTRAL_API_KEY"},
    "together": {"model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "env_key": "TOGETHER_API_KEY"},
    "openrouter": {"model": "anthropic/claude-3.5-sonnet", "env_key": "OPENROUTER_API_KEY"},
}


class Config(BaseModel):
    provider: str = "openai"
    model: str = ""
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 8192
    system_prompt: str = "Anda adalah Faresta Code, AI coding assistant yang membantu user di terminal. Anda bisa menjalankan perintah shell, membaca/menulis file, mencari kode, dan mengakses web. Selalu jelaskan apa yang Anda lakukan. Gunakan Bahasa Indonesia untuk menjawab."
    tool_confirm: bool = False

    def model_post_init(self, __context):
        if not self.model:
            defaults = PROVIDER_DEFAULTS.get(self.provider, {})
            self.model = defaults.get("model", "gpt-4o")


def load_config() -> Config:
    provider = os.getenv("FARESTA_PROVIDER", "openai")
    api_key = os.getenv("FARESTA_API_KEY", "")

    if CONFIG_FILE.exists():
        import yaml
        with open(CONFIG_FILE) as f:
            data = yaml.safe_load(f) or {}
        provider = data.get("provider", provider)
        api_key = data.get("api_key", api_key) if not api_key else api_key

    if not api_key:
        defaults = PROVIDER_DEFAULTS.get(provider, {})
        env_var = defaults.get("env_key", "OPENAI_API_KEY")
        api_key = os.getenv(env_var, "")

    config = Config(provider=provider, api_key=api_key)
    return config


def save_config(config: Config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    import yaml
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config.model_dump(), f)
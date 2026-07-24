import os
from pathlib import Path
from pydantic import BaseModel

CONFIG_DIR = Path.home() / ".config" / "faresta"
CONFIG_FILE = CONFIG_DIR / "config.yml"
HISTORY_DIR = CONFIG_DIR / "history"


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
            default_models = {
                "openai": "gpt-4o",
                "anthropic": "claude-sonnet-4-20250514",
                "google": "gemini-2.5-flash",
            }
            self.model = default_models.get(self.provider, "gpt-4o")


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
        provider_api_key_env = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
        }
        env_var = provider_api_key_env.get(provider, "OPENAI_API_KEY")
        api_key = os.getenv(env_var, "")

    config = Config(provider=provider, api_key=api_key)
    return config


def save_config(config: Config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    import yaml
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config.model_dump(), f)
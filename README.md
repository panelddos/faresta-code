# Faresta Code

**AI CLI Assistant** — Agentic coding assistant dengan multi-provider LLM, tool calling, social media integration, dan interactive terminal.

Dibuat oleh [Faresta](https://github.com/panelddos).

## Fitur

- **Multi-provider**: OpenAI (GPT-4o), Anthropic (Claude), Google (Gemini)
- **Agentic mode**: AI bisa menjalankan tools secara otomatis
- **Tools lengkap**: baca/tulis/edit file, bash, glob, grep, web fetch & search
- **Social media**: Twitter/X, Telegram, Discord
- **Streaming response**: real-time output
- **Interactive chat** dengan context management

## Instalasi

### Dari PyPI (coming soon)

```bash
pip install faresta-code
```

### Dari GitHub langsung (recommended)

```bash
pip install git+https://github.com/panelddos/faresta-code.git
```

### Dari source

```bash
git clone https://github.com/panelddos/faresta-code.git
cd faresta-code
pip install -e .
```

## Konfigurasi

### LLM API Keys

Set via environment variable:

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Google
export GOOGLE_API_KEY=...
```

Atau via CLI:

```bash
faresta config-set --api-key sk-... --provider openai --model gpt-4o
```

### Social Media API Keys

```bash
# Twitter/X
export TWITTER_BEARER_TOKEN=...
export TWITTER_API_KEY=...
export TWITTER_API_SECRET=...
export TWITTER_ACCESS_TOKEN=...
export TWITTER_ACCESS_SECRET=...

# Telegram
export TELEGRAM_BOT_TOKEN=...

# Discord
export DISCORD_WEBHOOK_URL=...
```

## Penggunaan

### Interactive agentic chat

```bash
faresta chat
```

### Single question

```bash
faresta ask "Buatkan fungsi Python untuk reverse string"
```

### Pilih provider/model

```bash
faresta chat --provider anthropic --model claude-sonnet-4-20250514
faresta ask "Jelaskan React hooks" --provider google --model gemini-2.0-flash
```

### Lihat config

```bash
faresta config-show
```

## Social Media Tools

AI agent bisa menggunakan social tools jika API keys sudah diset:

- **Twitter**: `twitter post "text"` atau `twitter search "query"`
- **Telegram**: `telegram send --chat_id CHAT_ID --text "message"`
- **Discord**: `discord send --text "message"` (pakai DISCORD_WEBHOOK_URL)

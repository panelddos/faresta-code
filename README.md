# Faresta Code

**AI CLI Assistant** — Agentic coding assistant dengan multi-provider LLM, tool calling, dan interactive terminal.

Dibuat oleh [Faresta](https://github.com/panelddos).

## Fitur

- **Multi-provider**: OpenAI (GPT-4o), Anthropic (Claude), Google (Gemini)
- **Agentic mode**: AI bisa menjalankan tools secara otomatis
- **Tools lengkap**: baca/tulis/edit file, bash, glob, grep, web fetch & search
- **Streaming response**: real-time output
- **Interactive chat** dengan context management

## Instalasi

```bash
pip install faresta-code
```

Atau instal dari source:

```bash
git clone https://github.com/panelddos/faresta-code.git
cd faresta-code
pip install -e .
```

## Konfigurasi

Set API key via environment variable:

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

# Faresta Code

**AI CLI Assistant** — Multi-provider LLM dengan interface interaktif di terminal.

Dibuat oleh [Faresta](https://github.com/panelddos).

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

### Interactive chat

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
faresta config
```

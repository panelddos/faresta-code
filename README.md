# Faresta Code

**AI CLI Assistant** — Agentic coding assistant dengan multi-provider LLM, tool calling, git integration, social media, dan interactive terminal.

Dibuat oleh [Faresta](https://github.com/panelddos).

## Fitur

- **Multi-provider LLM**: OpenAI (GPT-4o), Anthropic (Claude), Google (Gemini), Groq, xAI (Grok), NVIDIA, DeepSeek, Mistral, Together, OpenRouter
- **Agentic mode**: AI menjalankan tools secara otomatis dengan error recovery
- **Tools lengkap**: baca/tulis/edit file, bash, glob, grep, web fetch & search
- **Git integration**: status, diff, commit, log, branch management
- **Lint/Test auto-detection**: deteksi & jalankan pytest, ruff, eslint, npm test, dll
- **Permission system**: kontrol tool mana yang boleh dijalankan per proyek
- **Project config**: `faresta.json` untuk setting per proyek
- **Cost tracking**: pantau token usage dan biaya per sesi
- **Session persistence**: simpan/resume sesi chat
- **Social media**: Twitter/X, Telegram, Discord
- **Streaming response**: real-time output
- **Interactive chat** dengan slash commands

## Instalasi

### Cara 1: One-liner via curl (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/panelddos/faresta-code/main/install.sh | sh
```

Installasi otomatis:
- Clone repo ke `~/.faresta/`
- Buat Python virtual environment
- Install dependencies
- Buat wrapper script di `~/.local/bin/faresta`

Setelah selesai, pastikan `~/.local/bin` ada di PATH kamu:
```bash
export PATH="$PATH:$HOME/.local/bin"
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc  # atau ~/.zshrc
source ~/.bashrc
```

### Cara 2: Langsung dari GitHub

```bash
pip install git+https://github.com/panelddos/faresta-code.git
```

### Cara 3: Dari source

```bash
git clone https://github.com/panelddos/faresta-code.git
cd faresta-code
pip install -e .
```

### Cara 4: Dari PyPI (coming soon)

```bash
pip install faresta-code
```

## Konfigurasi

### LLM API Keys

Set minimal satu API key via environment variable:

```bash
# OpenAI (default)
export OPENAI_API_KEY=sk-...

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Google
export GOOGLE_API_KEY=...
```

Atau simpan via CLI (config akan disimpan di `~/.config/faresta/config.yml`):

```bash
faresta config-set --api-key sk-... --provider openai --model gpt-4o
```

### Project Config (faresta.json)

Buat file `faresta.json` di root proyek kamu untuk konfigurasi per-proyek:

```bash
# Init dengan default
faresta project init

# Set default provider
faresta project init anthropic

# Izinkan tool tanpa konfirmasi
faresta project allow bash
faresta project allow write

# Tolak tool tertentu
faresta project deny web_search
```

Contoh `faresta.json`:
```json
{
  "permissions": {
    "allow": ["bash", "write", "read", "edit"],
    "deny": ["web_search"],
    "ask": ["git_commit", "bash"]
  },
  "default_provider": "anthropic",
  "default_model": "claude-sonnet-4-20250514"
}
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

### Chat dengan provider berbeda

```bash
faresta chat --provider anthropic --model claude-sonnet-4-20250514
faresta chat --provider google --model gemini-2.5-flash
```

### Single question

```bash
faresta ask "Buatkan fungsi Python untuk reverse string"
faresta ask "Apa error di file ini?" -p anthropic
```

### Tanpa konfirmasi tool

```bash
faresta ask "Cari semua file .py" -y
faresta chat -y
```

### Resume session sebelumnya

```bash
# Lihat session tersimpan
faresta session

# Resume session
faresta chat --resume 1721800000
```

## Slash Commands

Di dalam mode `chat`, tersedia perintah berikut:

| Command | Deskripsi |
|---------|-----------|
| `/clear` | Reset conversation context |
| `/help` | Tampilkan daftar commands |
| `/cost` | Tampilkan token usage dan biaya |
| `/tokens` | Tampilkan statistik context saat ini |
| `/save` | Simpan session saat ini |
| `/sessions` | List semua session tersimpan |
| `/project-config` | Tampilkan config proyek |

## Tools yang Tersedia

### Core Tools
- **read** — Baca isi file
- **write** — Tulis file baru
- **edit** — Cari & ganti teks dalam file
- **glob** — Cari file dengan pattern
- **grep** — Cari konten file dengan regex
- **ls** — List directory
- **bash** — Jalankan perintah shell
- **web_fetch** — Ambil konten dari URL
- **web_search** — Cari informasi di web

### Git Tools
- **git_status** — Lihat status repository
- **git_diff** — Lihat perubahan yang belum di-stage
- **git_commit** — Stage semua perubahan dan commit
- **git_log** — Riwayat commit
- **git_branch** — List, create, switch, delete branch

### Development Tools
- **lint_test** — Auto-detect dan jalankan linter/tests

### Social Tools
- **twitter** — Post tweet, search tweets
- **telegram** — Kirim pesan via bot
- **discord** — Kirim pesan via webhook

## Uninstall

```bash
# Hapus installasi curl-based
rm -rf ~/.faresta
rm -f ~/.local/bin/faresta

# Atau via pip
pip uninstall faresta-code

# Hapus config
rm -rf ~/.config/faresta
```

## Development

```bash
git clone https://github.com/panelddos/faresta-code.git
cd faresta-code
python3 -m venv venv
source venv/bin/activate
pip install -e .
faresta chat
```

## Lisensi

MIT License — see [LICENSE](LICENSE) for details.

---

**Faresta Code** — *AI coding assistant di terminal kamu.*
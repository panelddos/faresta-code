# Faresta Code

**AI CLI Assistant** — Agentic coding assistant with multi-provider LLM, tool calling, git integration, social media, and interactive terminal.

Dibuat oleh [Faresta](https://github.com/panelddos).

## Instalasi

### Linux / macOS (curl | sh)

```bash
curl -fsSL https://raw.githubusercontent.com/panelddos/faresta-code/main/install.sh | sh
```

Untuk mengatur direktori instalasi:
```bash
curl -fsSL https://raw.githubusercontent.com/panelddos/faresta-code/main/install.sh | FARESTA_DIR=~/.faresta sh
```

Setelah selesai, pastikan `~/.local/bin` ada di PATH:
```bash
export PATH="$PATH:$HOME/.local/bin"
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
source ~/.bashrc
```

### Windows PowerShell

```powershell
iwr -Uri "https://raw.githubusercontent.com/panelddos/faresta-code/main/install.ps1" -OutFile "$env:TEMP\install_faresta.ps1"
powershell -ExecutionPolicy Bypass -File "$env:TEMP\install_faresta.ps1"
```

Atau satu baris:
```powershell
& ([scriptblock]::Create((Invoke-WebRequest -Uri "https://raw.githubusercontent.com/panelddos/faresta-code/main/install.ps1").Content))
```

### macOS (Homebrew)

```bash
# Coming soon: brew install faresta-code/tap/faresta
```

### Dari Source

```bash
git clone https://github.com/panelddos/faresta-code.git
cd faresta-code
pip install -e .
```

## Quick Start

Set API key lalu jalankan:

```bash
export OPENAI_API_KEY=sk-...
faresta chat
```

Atau set via CLI:
```bash
faresta config-set --api-key sk-... --provider openai --model gpt-4o
```

Faresta Code mendukung banyak provider:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
faresta chat --provider anthropic

export GOOGLE_API_KEY=...
faresta chat --provider google
```

## Fitur

- **Multi-provider LLM**: OpenAI (GPT-4o, o3-mini), Anthropic (Claude), Google (Gemini), Groq, xAI (Grok), NVIDIA, DeepSeek, Mistral, Together, OpenRouter
- **Agentic mode**: AI menjalankan tools secara otomatis dengan error recovery
- **Project-aware**: AI scan struktur proyek (tree, dependencies, README) via `project_index`
- **Auto-verification**: Setiap edit/write otomatis di-lint untuk deteksi error
- **Effort system**: Kontrol seberapa dalam AI berpikir (low/medium/high)
- **Tools lengkap**: baca/tulis/edit file, bash, glob, grep, web fetch & search, sub-agent
- **Git integration**: status, diff, commit, log, branch management
- **Lint/Test auto-detection**: deteksi & jalankan pytest, ruff, eslint, npm test, dll
- **Session persistence**: simpan/resume sesi chat
- **Cost tracking**: pantau token usage dan biaya per sesi
- **Social media**: Twitter/X, Telegram, Discord
- **Terminal UI**: full-screen alternate buffer, status bar, thinking spinner
- **Streaming response**: real-time output

## Penggunaan

### Interactive chat

```bash
faresta chat
```

### Dengan provider berbeda

```bash
faresta chat --provider anthropic --model claude-sonnet-4-20250514
faresta chat --provider google --model gemini-2.5-flash
faresta chat --provider groq --model llama-3.3-70b-versatile
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

### Effort level

```bash
faresta config-set --effort high
```

Atau di dalam chat: `/effort`

### Resume session sebelumnya

```bash
# Lihat session tersimpan
faresta session

# Resume session
faresta chat --resume 1721800000
```

## Slash Commands (Interactive Chat)

| Command | Deskripsi |
|---------|-----------|
| `/help` | Tampilkan daftar commands |
| `/login` | Set API key + pilih provider & model |
| `/provider` | Ganti provider AI |
| `/model` | Ganti model AI |
| `/effort` | Set effort: low/medium/high |
| `/clear` | Reset percakapan |
| `/cost` | Lihat token usage & biaya |
| `/tokens` | Statistik konteks |
| `/save` | Simpan sesi ini |
| `/sessions` | Daftar/resume/delete sesi tersimpan |
| `/allow` | Izinkan tool tanpa konfirmasi (per proyek) |
| `/deny` | Tolak tool (per proyek) |
| `/project` | Lihat/config project faresta.json |
| `/export` | Export chat ke file .md |
| `exit/quit` | Keluar |

## CLI Commands

| Command | Deskripsi |
|---------|-----------|
| `faresta chat` | Interactive agentic chat |
| `faresta ask "..."` | Single question |
| `faresta config-show` | Lihat config |
| `faresta config-set --key val` | Set config value |
| `faresta project init` | Buat faresta.json |
| `faresta project allow <tool>` | Izinkan tool |
| `faresta project deny <tool>` | Tolak tool |
| `faresta session` | List sessions |

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
- **project_index** — Scan struktur proyek (tree, README, deps)
- **read_image** — Baca & analisis gambar/screenshot
- **subagent** — Delegasikan tugas kompleks ke sub-agent

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

## Konfigurasi

### API Keys via Environment

```bash
# OpenAI (default)
export OPENAI_API_KEY=sk-...

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Google
export GOOGLE_API_KEY=...

# Groq
export GROQ_API_KEY=gsk_...

# xAI (Grok)
export XAI_API_KEY=...

# NVIDIA
export NVIDIA_API_KEY=...

# DeepSeek
export DEEPSEEK_API_KEY=...

# Mistral
export MISTRAL_API_KEY=...

# Together AI
export TOGETHER_API_KEY=...

# OpenRouter
export OPENROUTER_API_KEY=...
```

### Project Config (faresta.json)

Buat file `faresta.json` di root proyek:

```bash
faresta project init
faresta project allow bash
faresta project deny web_search
```

Contoh `faresta.json`:
```json
{
  "permissions": {
    "allow": ["bash", "write", "read", "edit"],
    "deny": ["web_search"],
    "ask": ["git_commit"]
  },
  "default_provider": "anthropic",
  "default_model": "claude-sonnet-4-20250514"
}
```

## Uninstall

**Linux / macOS:**
```bash
rm -rf ~/.faresta
rm -f ~/.local/bin/faresta
rm -rf ~/.config/faresta
```

**Windows PowerShell:**
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.faresta"
Remove-Item -Force "$env:USERPROFILE\.local\bin\faresta.exe"
Remove-Item -Recurse -Force "$env:USERPROFILE\.config\faresta"
```

**Via pip:**
```bash
pip uninstall faresta-code -y
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

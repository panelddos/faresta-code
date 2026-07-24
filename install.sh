#!/bin/sh
set -eu

REPO="https://github.com/panelddos/faresta-code.git"
INSTALL_DIR="${FARESTA_DIR:-$HOME/.faresta}"
BIN_DIR="${FARESTA_BIN:-$HOME/.local/bin}"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

printf "${CYAN}╔══════════════════════════════════════╗${NC}\n"
printf "${CYAN}║     Faresta Code Installer v0.4.0   ║${NC}\n"
printf "${CYAN}╚══════════════════════════════════════╝${NC}\n"
printf "\n"

# Check Python
if ! command -v python3 >/dev/null 2>&1; then
    printf "${YELLOW}Python 3.10+ is required but not found.${NC}\n"
    printf "Install it first:\n"
    printf "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv\n"
    printf "  macOS:          brew install python3\n"
    printf "  Windows:        https://python.org/downloads/\n"
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    printf "${YELLOW}Python 3.10+ required, found %s${NC}\n" "$PY_VERSION"
    exit 1
fi

printf "${GREEN}✓${NC} Python %s detected\n" "$PY_VERSION"

# Create bin dir
mkdir -p "$BIN_DIR"

# Clone or update repo
if [ -d "$INSTALL_DIR" ]; then
    printf "Updating existing installation...\n"
    cd "$INSTALL_DIR"
    git pull --ff-only 2>/dev/null || true
else
    printf "Cloning Faresta Code from GitHub...\n"
    git clone --depth 1 "$REPO" "$INSTALL_DIR"
fi

# Create virtualenv if needed
VENV_DIR="$INSTALL_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    printf "Creating virtual environment...\n"
    python3 -m venv "$VENV_DIR"
fi

# Install/upgrade
printf "Installing dependencies...\n"
printf "  (this may take a few minutes, especially for Rust-based packages)\n\n"
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel --progress-bar on 2>&1 | sed 's/^/  [pip] /'
printf "\n"
"$VENV_DIR/bin/pip" install -e "$INSTALL_DIR" --progress-bar on 2>&1 | sed 's/^/  [pip] /'
printf "\n"

# Create wrapper script
WRAPPER="$BIN_DIR/faresta"
cat > "$WRAPPER" << 'WRAPPEREOF'
#!/usr/bin/env bash
export FARESTA_DIR="$(cd "$(dirname "$(dirname "$(readlink -f "$0")")")" && pwd)"
exec "$FARESTA_DIR/venv/bin/faresta" "$@"
WRAPPEREOF
chmod +x "$WRAPPER"

# Add to PATH hint
printf "\n"
printf "${GREEN}✓${NC} Faresta Code installed successfully!\n"
printf "\n"
printf "  Run:  ${CYAN}faresta chat${NC}\n"
printf "  Help: ${CYAN}faresta --help${NC}\n"
printf "\n"

case :$PATH: in
    *:$BIN_DIR:*)
        ;;
    *)
        printf "${YELLOW}Note:${NC} Add %s to your PATH:\n" "$BIN_DIR"
        printf "  export PATH=\"\$PATH:%s\"\n" "$BIN_DIR"
        printf "\n"
        printf "Add it to ~/.bashrc or ~/.zshrc to make it permanent:\n"
        printf "  echo 'export PATH=\"\$PATH:%s\"' >> ~/.bashrc\n" "$BIN_DIR"
        printf "  source ~/.bashrc\n"
        ;;
esac

printf "\n"
printf "Set your API key and start using:\n"
printf "  export OPENAI_API_KEY=sk-...\n"
printf "  ${CYAN}faresta chat${NC}\n"
printf "\n"
printf "${CYAN}Selamat coding!${NC}\n"
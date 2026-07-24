#!/bin/sh
# Faresta Code Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/panelddos/faresta-code/main/install.sh | sh
set -eu

REPO="https://github.com/panelddos/faresta-code.git"
INSTALL_DIR="${FARESTA_DIR:-$HOME/.faresta}"
BIN_DIR="${FARESTA_BIN:-$HOME/.local/bin}"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

printf "${CYAN}╔══════════════════════════════════════╗${NC}\n"
printf "${CYAN}║     Faresta Code Installer v0.6.0   ║${NC}\n"
printf "${CYAN}╚══════════════════════════════════════╝${NC}\n"
printf "\n"

# --- Check prerequisites ---
check_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        printf "${RED}✖ Required: %s is not installed${NC}\n" "$1"
        return 1
    fi
    return 0
}

MISSING=""
for cmd in python3 git; do
    check_cmd "$cmd" || MISSING="$MISSING $cmd"
done

if [ -n "$MISSING" ]; then
    printf "\n${YELLOW}Install missing dependencies:${NC}\n"
    if command -v apt >/dev/null 2>&1; then
        printf "  sudo apt install%s\n" "$MISSING"
    elif command -v brew >/dev/null 2>&1; then
        printf "  brew install%s\n" "$MISSING"
    elif command -v dnf >/dev/null 2>&1; then
        printf "  sudo dnf install%s\n" "$MISSING"
    elif command -v yum >/dev/null 2>&1; then
        printf "  sudo yum install%s\n" "$MISSING"
    elif command -v pacman >/dev/null 2>&1; then
        printf "  sudo pacman -S%s\n" "$MISSING"
    else
        printf "  Install%s for your system manually.\n" "$MISSING"
    fi
    exit 1
fi

# Check Python version
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    printf "${RED}✖ Python 3.10+ required, found %s${NC}\n" "$PY_VERSION"
    printf "${YELLOW}Upgrade Python:${NC}\n"
    printf "  Ubuntu/Debian: sudo apt install python3.11 python3-pip python3-venv\n"
    printf "  macOS:          brew install python@3.11\n"
    exit 1
fi
printf "${GREEN}✓${NC} Python %s\n" "$PY_VERSION"
printf "${GREEN}✓${NC} git\n"

# Create bin dir
mkdir -p "$BIN_DIR"

# Clone or update repo
if [ -d "$INSTALL_DIR/.git" ]; then
    printf "Updating existing installation at %s...\n" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    git pull --ff-only 2>/dev/null || printf "${YELLOW}⚠ Could not pull updates, using existing${NC}\n"
else
    printf "Cloning Faresta Code to %s...\n" "$INSTALL_DIR"
    rm -rf "$INSTALL_DIR" 2>/dev/null || true
    git clone --depth 1 "$REPO" "$INSTALL_DIR"
fi

printf "\n"

# Create virtualenv if needed
VENV_DIR="$INSTALL_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    printf "Creating Python virtual environment...\n"
    python3 -m venv "$VENV_DIR"
fi

# Install/upgrade dependencies
printf "Installing dependencies (this may take a minute)...\n"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip setuptools wheel 2>&1 | sed 's/^/  /'
"$VENV_DIR/bin/pip" install --quiet -e "$INSTALL_DIR" 2>&1 | sed 's/^/  /'
printf "\n"

# Create wrapper script
WRAPPER="$BIN_DIR/faresta"
cat > "$WRAPPER" << WRAPPEREOF
#!/usr/bin/env bash
exec "$INSTALL_DIR/venv/bin/faresta" "\$@"
WRAPPEREOF
chmod +x "$WRAPPER"

printf "${GREEN}✓${NC} Installed to ${CYAN}%s${NC}\n" "$INSTALL_DIR"
printf "${GREEN}✓${NC} Wrapper at  ${CYAN}%s${NC}\n" "$WRAPPER"

# PATH hint
printf "\n"
case :$PATH: in
    *:$BIN_DIR:*)
        printf "${GREEN}✓${NC} %s is in PATH\n" "$BIN_DIR"
        ;;
    *)
        printf "${YELLOW}⚠ %s is NOT in PATH${NC}\n" "$BIN_DIR"
        printf "  Add this to your shell config (~/.bashrc, ~/.zshrc, etc.):\n"
        printf "  export PATH=\"\$PATH:%s\"\n" "$BIN_DIR"
        printf "\n"
        printf "  Or run now:\n"
        printf "  export PATH=\"\$PATH:%s\"\n" "$BIN_DIR"
        ;;
esac

printf "\n"
printf "╔══════════════════════════════════════╗\n"
printf "║  ${GREEN}Faresta Code installed!${NC}              ║\n"
printf "║                                      ║\n"
printf "║  ${CYAN}1. Set API key${NC}                       ║\n"
printf "║     export OPENAI_API_KEY=sk-...     ║\n"
printf "║                                      ║\n"
printf "║  ${CYAN}2. Start chatting${NC}                    ║\n"
printf "║     faresta chat                     ║\n"
printf "║                                      ║\n"
printf "║  ${CYAN}3. See all commands${NC}                  ║\n"
printf "║     faresta --help                   ║\n"
printf "╚══════════════════════════════════════╝\n"
printf "\n"
printf "${CYAN}Selamat coding!${NC}\n"

#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/panelddos/faresta-code.git"
INSTALL_DIR="${FARESTA_DIR:-$HOME/.faresta}"
BIN_DIR="${FARESTA_BIN:-$HOME/.local/bin}"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Faresta Code Installer v0.4.0   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo -e "${YELLOW}Python 3.10+ is required but not found.${NC}"
    echo "Install it first:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  macOS:          brew install python3"
    echo "  Windows:        https://python.org/downloads/"
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo -e "${YELLOW}Python 3.10+ required, found $PY_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python $PY_VERSION detected"

# Create bin dir
mkdir -p "$BIN_DIR"

# Clone or update repo
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --ff-only 2>/dev/null || true
else
    echo "Cloning Faresta Code from GitHub..."
    git clone --depth 1 "$REPO" "$INSTALL_DIR"
fi

# Create virtualenv if needed
VENV_DIR="$INSTALL_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Install/upgrade
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install --quiet -e "$INSTALL_DIR"

# Create wrapper script
WRAPPER="$BIN_DIR/faresta"
cat > "$WRAPPER" << 'WRAPPEREOF'
#!/usr/bin/env bash
export FARESTA_DIR="$(cd "$(dirname "$(dirname "$(readlink -f "$0")")")" && pwd)"
exec "$FARESTA_DIR/venv/bin/faresta" "$@"
WRAPPEREOF
chmod +x "$WRAPPER"

# Add to PATH hint
echo ""
echo -e "${GREEN}✓${NC} Faresta Code installed successfully!"
echo ""
echo -e "  Run:  ${CYAN}faresta chat${NC}"
echo -e "  Help: ${CYAN}faresta --help${NC}"
echo ""

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Note:${NC} Add $BIN_DIR to your PATH:"
    echo "  export PATH=\"\$PATH:$BIN_DIR\""
    echo ""
    echo "Add it to ~/.bashrc or ~/.zshrc to make it permanent:"
    echo "  echo 'export PATH=\"\$PATH:$BIN_DIR\"' >> ~/.bashrc"
    echo "  source ~/.bashrc"
fi

echo -e "Set your API key and start using:"
echo -e "  export OPENAI_API_KEY=sk-..."
echo -e "  ${CYAN}faresta chat${NC}"
echo ""
echo -e "${CYAN}Selamat coding!${NC}"
#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/debiddr5777/secaztool.git"
INSTALL_DIR="/tmp/secaz-install"

# ── helpers ──────────────────────────────────────────────────────────────────
red()    { printf "\033[31m%s\033[0m\n" "$*"; }
green()  { printf "\033[32m%s\033[0m\n" "$*"; }
blue()   { printf "\033[34m%s\033[0m\n" "$*"; }
yellow() { printf "\033[33m%s\033[0m\n" "$*"; }

# ── prerequisites ────────────────────────────────────────────────────────────
blue "==> Checking prerequisites..."

if [ "$(uname)" != "Linux" ]; then
    red "This tool only works on Linux."
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    red "python3 is required but not found."
    red "Install it with your package manager, e.g.:"
    red "  sudo apt install python3 python3-pip   (Debian/Ubuntu)"
    red "  sudo dnf install python3 python3-pip   (Fedora)"
    exit 1
fi

PYVER=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if [ "$(echo "$PYVER < 3.8" | bc -l 2>/dev/null 2>/dev/null)" = "1" ] 2>/dev/null; then
    red "Python 3.8+ required, found $PYVER"
    exit 1
fi

PIP="pip3"
if ! command -v pip3 &>/dev/null; then
    if python3 -m pip --version &>/dev/null; then
        PIP="python3 -m pip"
    else
        red "pip is required but not found."
        exit 1
    fi
fi

green "  python3 $PYVER found"
green "  pip found"

# ── fzf (optional) ───────────────────────────────────────────────────────────
if ! command -v fzf &>/dev/null; then
    blue "==> fzf not found — installing (optional, enables multi-select)..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y fzf 2>/dev/null || true
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y fzf 2>/dev/null || true
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm fzf 2>/dev/null || true
    else
        echo "  (skip — install fzf manually for the best experience)"
    fi
fi

# ── source ───────────────────────────────────────────────────────────────────
SRC_DIR=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd 2>/dev/null || echo "")"
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/setup.py" ] && grep -q 'secaz' "$SCRIPT_DIR/setup.py" 2>/dev/null; then
    SRC_DIR="$SCRIPT_DIR"
    blue "==> Using local source at $SRC_DIR"
else
    blue "==> Fetching secaz from GitHub..."
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
    fi
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
    SRC_DIR="$INSTALL_DIR"
fi

cd "$SRC_DIR"

# ── install ──────────────────────────────────────────────────────────────────
blue "==> Installing secaz..."

if [ "$(id -u)" -eq 0 ]; then
    $PIP install . --break-system-packages 2>/dev/null || $PIP install .
else
    if command -v sudo &>/dev/null; then
        sudo $PIP install . --break-system-packages 2>/dev/null || sudo $PIP install .
    else
        $PIP install --user . --break-system-packages 2>/dev/null || $PIP install --user .
    fi
fi

# ── ensure PATH ──────────────────────────────────────────────────────────────
blue "==> Ensuring secaz is on PATH..."

SHELL_RC=""
if [ -n "${ZSH_VERSION-}" ] || [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "${BASH_VERSION-}" ] || [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_RC="$HOME/.bash_profile"
fi

SECAZ_PATH=""
if command -v secaz &>/dev/null; then
    SECAZ_PATH=$(command -v secaz)
    green "  secaz found at $SECAZ_PATH"
else
    for dir in "$HOME/.local/bin" "/usr/local/bin" "/usr/bin"; do
        if [ -x "$dir/secaz" ]; then
            SECAZ_PATH="$dir/secaz"
            break
        fi
    done
fi

if [ -z "$SECAZ_PATH" ]; then
    SITE_BIN=$(python3 -m site --user-base 2>/dev/null)/bin
    if [ -x "$SITE_BIN/secaz" ]; then
        SECAZ_PATH="$SITE_BIN/secaz"
    fi
fi

if [ -n "$SECAZ_PATH" ]; then
    BIN_DIR=$(dirname "$SECAZ_PATH")
    if [ "$BIN_DIR" != "/usr/local/bin" ] && [ "$BIN_DIR" != "/usr/bin" ] && [ "$BIN_DIR" != "/bin" ]; then
        if [ -n "$SHELL_RC" ]; then
            if ! grep -q "export PATH=.*$BIN_DIR" "$SHELL_RC" 2>/dev/null; then
                echo "" >> "$SHELL_RC"
                echo "# Added by secaz installer" >> "$SHELL_RC"
                echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
                green "  Added $BIN_DIR to PATH in $SHELL_RC"
            else
                green "  $BIN_DIR already on PATH in $SHELL_RC"
            fi
        else
            yellow "  Add the following to your shell rc file:"
            echo "  export PATH=\"$BIN_DIR:\$PATH\""
        fi
    fi
fi

# ── verify ───────────────────────────────────────────────────────────────────
echo ""
if command -v secaz &>/dev/null || [ -n "$SECAZ_PATH" ]; then
    green "╔══════════════════════════════════════════╗"
    green "║   SECAZ installed successfully!          ║"
    green "╠══════════════════════════════════════════╣"
    green "║   Run:  secaz                            ║"
    green "║   Help: secaz --help                     ║"
    green "╚══════════════════════════════════════════╝"
else
    red "╔══════════════════════════════════════════╗"
    red "║   Install finished but secaz wasn't      ║"
    red "║   found on PATH. Try opening a new       ║"
    red "║   terminal or run:                       ║"
    if [ -n "$SHELL_RC" ]; then
        red "║   source $SHELL_RC     ║"
    fi
    red "║   secaz --help                           ║"
    red "╚══════════════════════════════════════════╝"
fi

# ── cleanup ──────────────────────────────────────────────────────────────────
if [ "$SRC_DIR" = "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
fi

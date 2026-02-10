#!/bin/bash
#
# GeekCode Installation Script
#
# Installs the geekcode binary to /usr/local/bin (or ~/.local/bin)
#
# Usage:
#   curl -fsSL https://get.geekcode.dev | sh
#   curl -fsSL https://raw.githubusercontent.com/sur950/GeekCode/main/install/install.sh | sh
#

set -e

# Configuration
GEEKCODE_VERSION="${GEEKCODE_VERSION:-latest}"
GITHUB_REPO="sur950/GeekCode"
INSTALL_DIR="${INSTALL_DIR:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Detect OS and architecture
detect_platform() {
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)

    case "$ARCH" in
        x86_64)  ARCH="amd64" ;;
        aarch64) ARCH="arm64" ;;
        arm64)   ARCH="arm64" ;;
        *)       error "Unsupported architecture: $ARCH" ;;
    esac

    case "$OS" in
        darwin) PLATFORM="darwin-$ARCH" ;;
        linux)  PLATFORM="linux-$ARCH" ;;
        *)      error "Unsupported OS: $OS" ;;
    esac

    info "Detected platform: $PLATFORM"
}

# Determine install directory
determine_install_dir() {
    if [ -n "$INSTALL_DIR" ]; then
        return
    fi

    # Prefer /usr/local/bin if writable, else ~/.local/bin
    if [ -w "/usr/local/bin" ]; then
        INSTALL_DIR="/usr/local/bin"
    elif [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
        INSTALL_DIR="$HOME/.local/bin"
    else
        error "Cannot determine install directory. Set INSTALL_DIR environment variable."
    fi

    info "Install directory: $INSTALL_DIR"
}

# Get latest version from GitHub
get_latest_version() {
    if [ "$GEEKCODE_VERSION" = "latest" ]; then
        GEEKCODE_VERSION=$(curl -sL "https://api.github.com/repos/$GITHUB_REPO/releases/latest" | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
        if [ -z "$GEEKCODE_VERSION" ]; then
            error "Failed to fetch latest version"
        fi
    fi
    info "Version: $GEEKCODE_VERSION"
}

# Download and install
install_binary() {
    TMP_DIR=$(mktemp -d)
    trap "rm -rf $TMP_DIR" EXIT

    BINARY_NAME="geekcode-${GEEKCODE_VERSION}-${PLATFORM}"
    DOWNLOAD_URL="https://github.com/$GITHUB_REPO/releases/download/v${GEEKCODE_VERSION}/${BINARY_NAME}.tar.gz"

    info "Downloading from $DOWNLOAD_URL..."
    curl -sL "$DOWNLOAD_URL" -o "$TMP_DIR/geekcode.tar.gz" || {
        # Fallback: try without version prefix
        DOWNLOAD_URL="https://github.com/$GITHUB_REPO/releases/download/${GEEKCODE_VERSION}/${BINARY_NAME}.tar.gz"
        curl -sL "$DOWNLOAD_URL" -o "$TMP_DIR/geekcode.tar.gz" || error "Download failed"
    }

    info "Extracting..."
    tar -xzf "$TMP_DIR/geekcode.tar.gz" -C "$TMP_DIR"

    info "Installing to $INSTALL_DIR..."
    if [ -w "$INSTALL_DIR" ]; then
        mv "$TMP_DIR/geekcode" "$INSTALL_DIR/"
        chmod +x "$INSTALL_DIR/geekcode"
    else
        sudo mv "$TMP_DIR/geekcode" "$INSTALL_DIR/"
        sudo chmod +x "$INSTALL_DIR/geekcode"
    fi

    success "Installed geekcode to $INSTALL_DIR/geekcode"
}

# Verify installation
verify_install() {
    if command -v geekcode &> /dev/null; then
        VERSION=$(geekcode --version 2>&1 || echo "unknown")
        success "geekcode installed successfully: $VERSION"
    else
        warn "geekcode installed but not in PATH"
        warn "Add $INSTALL_DIR to your PATH:"
        echo ""
        echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
        echo ""
    fi
}

# Create global config directory
setup_config() {
    CONFIG_DIR="$HOME/.geekcode"
    if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR"
        cat > "$CONFIG_DIR/config.yaml" << 'EOF'
# GeekCode Global Configuration
# API keys can also be set via environment variables:
#   OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY
#   OPENROUTER_API_KEY, TOGETHER_API_KEY, GROQ_API_KEY

api:
  openai: null
  anthropic: null
  google: null
  openrouter: null
  together: null
  groq: null

defaults:
  model: claude-3-sonnet
  max_tokens: 4096

cache:
  enabled: true
  ttl_hours: 24
EOF
        success "Created config at $CONFIG_DIR/config.yaml"
    fi
}

# Print instructions
print_instructions() {
    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  GeekCode installed successfully!${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Quick start:"
    echo ""
    echo "  1. Set your API key (one-time):"
    echo "     geekcode config set api.anthropic sk-ant-... --global"
    echo "     # Or: export ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    echo "  2. Initialize a project:"
    echo "     cd your-project"
    echo "     geekcode init"
    echo ""
    echo "  3. Run a task:"
    echo "     geekcode \"Analyze this codebase\""
    echo ""
    echo "Everything is stored in .geekcode/ - no memory in terminal."
    echo ""
}

# Main
main() {
    echo ""
    echo -e "${BLUE}GeekCode Installer${NC}"
    echo ""

    detect_platform
    determine_install_dir
    get_latest_version
    install_binary
    setup_config
    verify_install
    print_instructions
}

main "$@"

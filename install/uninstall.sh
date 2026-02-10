#!/bin/bash
#
# GeekCode Uninstall Script
#
# Removes the geekcode binary, global config, and PATH entries.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/sur950/GeekCode/main/install/uninstall.sh | sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo -e "${BLUE}GeekCode Uninstaller${NC}"
echo ""

# Find and remove binary
BINARY_FOUND=false

for BIN_DIR in /usr/local/bin "$HOME/.local/bin"; do
    if [ -f "$BIN_DIR/geekcode" ]; then
        info "Found geekcode at $BIN_DIR/geekcode"
        if [ -w "$BIN_DIR/geekcode" ]; then
            rm -f "$BIN_DIR/geekcode"
        else
            sudo rm -f "$BIN_DIR/geekcode"
        fi
        success "Removed $BIN_DIR/geekcode"
        BINARY_FOUND=true
    fi
done

if [ "$BINARY_FOUND" = false ]; then
    warn "geekcode binary not found in /usr/local/bin or ~/.local/bin"
fi

# Remove global config
CONFIG_DIR="$HOME/.geekcode"
if [ -d "$CONFIG_DIR" ]; then
    info "Removing global config at $CONFIG_DIR..."
    rm -rf "$CONFIG_DIR"
    success "Removed $CONFIG_DIR"
else
    info "No global config found at $CONFIG_DIR"
fi

# Clean PATH entries from shell profiles
clean_path_from_file() {
    local file="$1"
    if [ -f "$file" ]; then
        # Remove lines that add geekcode-related paths
        if grep -q "geekcode" "$file" 2>/dev/null; then
            # Create backup
            cp "$file" "${file}.geekcode-backup"
            grep -v "geekcode" "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
            success "Cleaned geekcode entries from $file (backup at ${file}.geekcode-backup)"
        fi
    fi
}

info "Checking shell profiles for PATH entries..."
clean_path_from_file "$HOME/.bashrc"
clean_path_from_file "$HOME/.bash_profile"
clean_path_from_file "$HOME/.zshrc"
clean_path_from_file "$HOME/.profile"

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  GeekCode uninstalled successfully!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
echo ""
echo "What was removed:"
echo "  - geekcode binary from system PATH"
echo "  - Global config from ~/.geekcode/"
echo "  - PATH entries from shell profiles"
echo ""

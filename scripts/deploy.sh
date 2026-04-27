#!/usr/bin/env bash
# Deploy KachelmannWetter integration to Home Assistant config directory.
#
# Usage:
#   ./scripts/deploy.sh                          # default: /Volumes/config
#   ./scripts/deploy.sh /path/to/ha/config       # custom HA config path
#
# After deploying, restart Home Assistant to pick up the changes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE="$REPO_DIR/custom_components/kachelmannwetter"

HA_CONFIG="${1:-/Volumes/config}"
TARGET="$HA_CONFIG/custom_components/kachelmannwetter"

if [ ! -d "$HA_CONFIG" ]; then
    echo "ERROR: HA config directory not found: $HA_CONFIG"
    echo "Usage: $0 [/path/to/ha/config]"
    exit 1
fi

echo "Deploying KachelmannWetter integration..."
echo "  Source: $SOURCE"
echo "  Target: $TARGET"

# Create target directory if it doesn't exist
mkdir -p "$TARGET"
mkdir -p "$TARGET/translations"

# Remove old files and copy fresh
rm -rf "$TARGET"/*
cp -R "$SOURCE"/* "$TARGET/"

# Clean up pycache
find "$TARGET" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$TARGET" -name '*.pyc' -delete 2>/dev/null || true

echo ""
echo "Done. Restart Home Assistant to apply changes."

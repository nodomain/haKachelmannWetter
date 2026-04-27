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

# Sync files (delete removed files too)
rsync -av --delete \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    "$SOURCE/" "$TARGET/"

echo ""
echo "Done. Restart Home Assistant to apply changes."

#!/bin/bash
# =============================================================================
# Prepare Virgin DevContainer Repository
# =============================================================================
# This script prepares all BMAD files for checking into virgin-devcontainer
#
# Usage:
#   ./scripts/prepare-virgin-devcontainer.sh /path/to/virgin-devcontainer
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if target directory is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Target directory not provided${NC}"
    echo "Usage: $0 /path/to/virgin-devcontainer"
    exit 1
fi

TARGET_DIR="$1"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${GREEN}Preparing BMAD files for virgin-devcontainer...${NC}"
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"
echo ""

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${YELLOW}Target directory does not exist. Creating...${NC}"
    mkdir -p "$TARGET_DIR"
fi

# Check if target is a git repository
if [ ! -d "$TARGET_DIR/.git" ]; then
    echo -e "${YELLOW}Target is not a git repository. Initializing...${NC}"
    cd "$TARGET_DIR"
    git init
    cd "$SOURCE_DIR"
fi

echo -e "${GREEN}Copying BMAD doctrine (_bmad/)...${NC}"
# Copy _bmad folder (exclude _bmad-output and cache files)
# Use rsync if available, otherwise use cp with find
if command -v rsync &> /dev/null; then
    rsync -av --exclude='_bmad-output' \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        "$SOURCE_DIR/_bmad/" "$TARGET_DIR/_bmad/"
else
    # Fallback: use cp with proper directory structure
    mkdir -p "$TARGET_DIR/_bmad"
    cd "$SOURCE_DIR/_bmad"
    find . -type f \
        ! -path "*/_bmad-output/*" \
        ! -name "*.pyc" \
        ! -path "*/__pycache__/*" \
        -exec sh -c 'mkdir -p "$2/$(dirname "$1")" && cp "$3/$1" "$2/$1"' _ {} "$TARGET_DIR/_bmad" "$SOURCE_DIR/_bmad" \;
    cd "$SOURCE_DIR"
fi

echo -e "${GREEN}Copying Cursor rules (.cursor/rules/bmad/)...${NC}"
# Copy .cursor/rules/bmad folder
mkdir -p "$TARGET_DIR/.cursor/rules/bmad"
cp -r "$SOURCE_DIR/.cursor/rules/bmad/"* "$TARGET_DIR/.cursor/rules/bmad/"

echo -e "${GREEN}Copying setup scripts...${NC}"
# Copy bmad-setup.py
mkdir -p "$TARGET_DIR/scripts"
cp "$SOURCE_DIR/scripts/bmad-setup.py" "$TARGET_DIR/scripts/bmad-setup.py"
chmod +x "$TARGET_DIR/scripts/bmad-setup.py"

# Copy sync-behavioral-rules-to-template.sh (so projects can sync back)
if [ -f "$SOURCE_DIR/scripts/sync-behavioral-rules-to-template.sh" ]; then
    cp "$SOURCE_DIR/scripts/sync-behavioral-rules-to-template.sh" "$TARGET_DIR/scripts/sync-behavioral-rules-to-template.sh"
    chmod +x "$TARGET_DIR/scripts/sync-behavioral-rules-to-template.sh"
    echo -e "${GREEN}  ✓ Copied sync-behavioral-rules-to-template.sh${NC}"
fi

echo -e "${GREEN}Copying documentation...${NC}"
# Copy key documentation files
mkdir -p "$TARGET_DIR/docs"
cp "$SOURCE_DIR/docs/BMAD_CURSOR_INTEGRATION_EXPLAINED.md" "$TARGET_DIR/docs/" 2>/dev/null || true
cp "$SOURCE_DIR/docs/BMAD_DOCTRINE_INTEGRATION_SUMMARY.md" "$TARGET_DIR/docs/" 2>/dev/null || true
cp "$SOURCE_DIR/docs/VIRGIN_DEVCONTAINER_CHECKLIST.md" "$TARGET_DIR/docs/" 2>/dev/null || true
cp "$SOURCE_DIR/docs/VIRGIN_DEVCONTAINER_QUICK_REFERENCE.md" "$TARGET_DIR/docs/" 2>/dev/null || true
# Note: genImage doctrine is embedded in agent and workflow files, not separate doctrine folder

echo -e "${GREEN}Ensuring project-config.yaml is a template...${NC}"
# Ensure project-config.yaml has template values (not project-specific)
if [ -f "$TARGET_DIR/_bmad/_config/project-config.yaml" ]; then
    # Replace project-specific values with placeholders
    sed -i.bak \
        -e 's/name: "mem0-rag"/name: "your-project-name"/' \
        -e 's/display_name: ".*"/display_name: "Your Project Name"/' \
        -e 's/project_id: [0-9]*/project_id: null/' \
        -e 's/user_name: ".*"/user_name: "TeamLead"/' \
        "$TARGET_DIR/_bmad/_config/project-config.yaml" 2>/dev/null || true
    rm -f "$TARGET_DIR/_bmad/_config/project-config.yaml.bak"
fi

echo -e "${GREEN}Creating .gitignore entries if needed...${NC}"
# Ensure .gitignore includes _bmad-output
if [ -f "$TARGET_DIR/.gitignore" ]; then
    if ! grep -q "_bmad-output" "$TARGET_DIR/.gitignore"; then
        echo "" >> "$TARGET_DIR/.gitignore"
        echo "# BMAD generated output" >> "$TARGET_DIR/.gitignore"
        echo "_bmad-output/" >> "$TARGET_DIR/.gitignore"
    fi
else
    cat > "$TARGET_DIR/.gitignore" <<EOF
# BMAD generated output
_bmad-output/
EOF
fi

echo ""
echo -e "${GREEN}✅ Files prepared successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Review the copied files in: $TARGET_DIR"
echo "2. Update README.md with BMAD documentation"
echo "3. Commit and push to repository:"
echo "   cd $TARGET_DIR"
echo "   git add ."
echo "   git commit -m 'Add complete BMAD methodology integration'"
echo "   git push origin main"
echo ""


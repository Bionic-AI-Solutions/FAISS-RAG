#!/bin/bash
# =============================================================================
# Sync Behavioral Rules to Virgin DevContainer Template
# =============================================================================
# This script syncs behavioral rules (_bmad/integrations/*.mdc) to the
# virgin-devcontainer template repository to ensure new projects get the latest
# behavioral improvements.
#
# Usage:
#   ./scripts/sync-behavioral-rules-to-template.sh [--dry-run] [--check-only]
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VIRGIN_REPO_URL="https://github.com/Bionic-AI-Solutions/virgin-devcontainer.git"
VIRGIN_REPO_DIR="${HOME}/.bmad-cache/virgin-devcontainer"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BEHAVIORAL_RULES_DIR="${SOURCE_DIR}/_bmad/integrations"
BEHAVIORAL_RULES_PATTERN="*.mdc"

# Parse arguments
DRY_RUN=false
CHECK_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--dry-run] [--check-only]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}Sync Behavioral Rules to Virgin DevContainer Template${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo "Source: ${BEHAVIORAL_RULES_DIR}"
echo "Target: ${VIRGIN_REPO_DIR}/_bmad/integrations/"
echo ""

# Check if behavioral rules directory exists
if [ ! -d "${BEHAVIORAL_RULES_DIR}" ]; then
    echo -e "${RED}Error: Behavioral rules directory not found: ${BEHAVIORAL_RULES_DIR}${NC}"
    exit 1
fi

# Find all behavioral rule files
BEHAVIORAL_FILES=$(find "${BEHAVIORAL_RULES_DIR}" -name "${BEHAVIORAL_RULES_PATTERN}" -type f | sort)

if [ -z "$BEHAVIORAL_FILES" ]; then
    echo -e "${YELLOW}Warning: No behavioral rule files found matching ${BEHAVIORAL_RULES_PATTERN}${NC}"
    exit 0
fi

echo -e "${GREEN}Found behavioral rule files:${NC}"
echo "$BEHAVIORAL_FILES" | sed 's/^/  - /'
echo ""

# Clone or update virgin-devcontainer repository
if [ ! -d "${VIRGIN_REPO_DIR}" ]; then
    echo -e "${YELLOW}Virgin devcontainer repo not found. Cloning...${NC}"
    mkdir -p "$(dirname "${VIRGIN_REPO_DIR}")"
    if [ "$DRY_RUN" = false ]; then
        git clone "${VIRGIN_REPO_URL}" "${VIRGIN_REPO_DIR}"
    else
        echo -e "${BLUE}[DRY RUN] Would clone: ${VIRGIN_REPO_URL}${NC}"
    fi
else
    echo -e "${GREEN}Virgin devcontainer repo found. Updating...${NC}"
    if [ "$DRY_RUN" = false ]; then
        cd "${VIRGIN_REPO_DIR}"
        git fetch origin
        git checkout main
        git pull origin main
        cd "${SOURCE_DIR}"
    else
        echo -e "${BLUE}[DRY RUN] Would update repository${NC}"
    fi
fi

# Ensure target directory exists
TARGET_DIR="${VIRGIN_REPO_DIR}/_bmad/integrations"
if [ "$DRY_RUN" = false ]; then
    mkdir -p "${TARGET_DIR}"
else
    echo -e "${BLUE}[DRY RUN] Would create directory: ${TARGET_DIR}${NC}"
fi

# Sync each behavioral rule file
SYNCED_COUNT=0
UPDATED_COUNT=0
NEW_COUNT=0

for SOURCE_FILE in $BEHAVIORAL_FILES; do
    FILENAME=$(basename "${SOURCE_FILE}")
    TARGET_FILE="${TARGET_DIR}/${FILENAME}"
    
    # Check if file exists and is different
    if [ -f "${TARGET_FILE}" ]; then
        if ! cmp -s "${SOURCE_FILE}" "${TARGET_FILE}"; then
            echo -e "${YELLOW}  📝 Updating: ${FILENAME}${NC}"
            if [ "$DRY_RUN" = false ]; then
                cp "${SOURCE_FILE}" "${TARGET_FILE}"
            fi
            UPDATED_COUNT=$((UPDATED_COUNT + 1))
        else
            echo -e "${GREEN}  ✓ Unchanged: ${FILENAME}${NC}"
        fi
    else
        echo -e "${BLUE}  ➕ New file: ${FILENAME}${NC}"
        if [ "$DRY_RUN" = false ]; then
            cp "${SOURCE_FILE}" "${TARGET_FILE}"
        fi
        NEW_COUNT=$((NEW_COUNT + 1))
    fi
    SYNCED_COUNT=$((SYNCED_COUNT + 1))
done

echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}Sync Summary:${NC}"
echo -e "  Total files: ${SYNCED_COUNT}"
echo -e "  New files: ${NEW_COUNT}"
echo -e "  Updated files: ${UPDATED_COUNT}"
echo -e "  Unchanged files: $((SYNCED_COUNT - NEW_COUNT - UPDATED_COUNT))"
echo -e "${BLUE}=============================================================================${NC}"

# If check-only, exit here
if [ "$CHECK_ONLY" = true ]; then
    if [ $UPDATED_COUNT -gt 0 ] || [ $NEW_COUNT -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Changes detected. Run without --check-only to sync.${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ All behavioral rules are in sync.${NC}"
        exit 0
    fi
fi

# Commit and push changes (if not dry-run and changes exist)
if [ "$DRY_RUN" = false ] && [ $((NEW_COUNT + UPDATED_COUNT)) -gt 0 ]; then
    echo ""
    echo -e "${GREEN}Committing changes...${NC}"
    cd "${VIRGIN_REPO_DIR}"
    
    git add "${TARGET_DIR}"/*.mdc
    
    COMMIT_MSG="chore: sync behavioral rules from mem0-rag project

Synced behavioral rules to ensure new projects get latest improvements:
- Updated: ${UPDATED_COUNT} files
- New: ${NEW_COUNT} files

Source: ${SOURCE_DIR}
Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    
    if git diff --staged --quiet; then
        echo -e "${YELLOW}No changes to commit.${NC}"
    else
        git commit -m "${COMMIT_MSG}"
        echo ""
        echo -e "${GREEN}✅ Changes committed.${NC}"
        echo ""
        echo -e "${YELLOW}Next steps:${NC}"
        echo "  1. Review the changes:"
        echo "     cd ${VIRGIN_REPO_DIR}"
        echo "     git log -1"
        echo "     git diff HEAD~1"
        echo ""
        echo "  2. Push to repository:"
        echo "     git push origin main"
        echo ""
        echo "  3. Verify in GitHub:"
        echo "     ${VIRGIN_REPO_URL}"
    fi
    cd "${SOURCE_DIR}"
elif [ "$DRY_RUN" = true ]; then
    echo ""
    echo -e "${BLUE}[DRY RUN] Would commit and push changes${NC}"
fi

echo ""
echo -e "${GREEN}✅ Sync complete!${NC}"


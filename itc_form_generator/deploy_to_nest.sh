#!/bin/bash
# =============================================================================
# ITC Form Generator - NEST Deployment Script
# =============================================================================
# This script deploys the ITC Form Generator to NEST with MetaGen support.
#
# Prerequisites:
#   - Run this script on an OD or Devserver (not local Windows)
#   - Have access to fbsource repository
#   - Have NEST CLI installed (should be pre-installed on devservers)
#
# Usage:
#   chmod +x deploy_to_nest.sh
#   ./deploy_to_nest.sh
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   ITC Form Generator - NEST Deployment${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_NAME="itc_form_generator"

# Check if we're on a Meta machine
if [ ! -d ~/fbsource ]; then
    echo -e "${RED}Error: ~/fbsource not found. Are you on an OD/Devserver?${NC}"
    echo "This script must be run on a Meta internal machine."
    exit 1
fi

# Check if nest CLI is available
if ! command -v nest &> /dev/null; then
    echo -e "${RED}Error: 'nest' command not found.${NC}"
    echo "Please ensure NEST CLI is installed."
    exit 1
fi

echo -e "${GREEN}✓ Running on Meta internal machine${NC}"
echo -e "${GREEN}✓ NEST CLI available${NC}"
echo ""

# Destination in fbsource
DEST_DIR=~/fbsource/fbcode/datacenter_cx/tools/${APP_NAME}

echo -e "${YELLOW}Step 1: Setting up destination directory...${NC}"
mkdir -p $(dirname $DEST_DIR)

# If destination exists, ask before overwriting
if [ -d "$DEST_DIR" ]; then
    echo -e "${YELLOW}Warning: $DEST_DIR already exists.${NC}"
    read -p "Do you want to overwrite it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
    rm -rf "$DEST_DIR"
fi

echo -e "${YELLOW}Step 2: Copying application files...${NC}"
mkdir -p "$DEST_DIR"

# Copy all necessary files
cp -r "$SCRIPT_DIR/src" "$DEST_DIR/"
cp "$SCRIPT_DIR/webapp.py" "$DEST_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$DEST_DIR/"
cp "$SCRIPT_DIR/nest.json" "$DEST_DIR/"
cp "$SCRIPT_DIR/Dockerfile" "$DEST_DIR/"
cp "$SCRIPT_DIR/sample_soo.md" "$DEST_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/sample_points_list.csv" "$DEST_DIR/" 2>/dev/null || true

# Copy feedback and examples data if they exist
cp "$SCRIPT_DIR/feedback_data.json" "$DEST_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/learned_examples.json" "$DEST_DIR/" 2>/dev/null || true

echo -e "${GREEN}✓ Files copied to $DEST_DIR${NC}"
echo ""

echo -e "${YELLOW}Step 3: Verifying MetaGen availability...${NC}"
python3 -c "from metagen import MetaGenPlatform; print('MetaGen is available!')" 2>/dev/null && \
    echo -e "${GREEN}✓ MetaGen is available${NC}" || \
    echo -e "${YELLOW}⚠ MetaGen not available in current environment (will work in NEST)${NC}"
echo ""

echo -e "${YELLOW}Step 4: Deploying to NEST...${NC}"
cd "$DEST_DIR"

# Run nest deploy
echo "Running: nest deploy"
nest deploy

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Your app should now be available at:"
echo -e "${BLUE}  https://${APP_NAME}.nest.meta.net${NC}"
echo ""
echo -e "To check deployment status:"
echo -e "  ${YELLOW}nest status${NC}"
echo ""
echo -e "To view logs:"
echo -e "  ${YELLOW}nest logs${NC}"
echo ""
echo -e "MetaGen AI features are now enabled! 🚀"

#!/bin/bash

# Script to create GitHub repository for FAISS-RAG
# This script helps authenticate with GitHub and create the repository

set -e

GH_BIN="/tmp/gh_*/bin/gh"

# Check if GitHub CLI is available
if [ ! -f $GH_BIN ]; then
    echo "❌ GitHub CLI not found. Please run the setup first."
    exit 1
fi

# Check authentication
if ! $GH_BIN auth status &>/dev/null; then
    echo "🔐 GitHub authentication required"
    echo ""
    echo "You have two options:"
    echo ""
    echo "Option 1: Interactive login (recommended)"
    echo "  Run: $GH_BIN auth login"
    echo "  Follow the prompts to authenticate"
    echo ""
    echo "Option 2: Use a token"
    echo "  Run: $GH_BIN auth login --with-token < your_token.txt"
    echo "  Or: echo 'YOUR_TOKEN' | $GH_BIN auth login --with-token"
    echo ""
    echo "After authentication, run this script again."
    exit 1
fi

echo "✅ Authenticated with GitHub"
echo ""

# Create the repository
echo "📦 Creating repository: Bionic-AI-Solutions/FAISS-RAG"
$GH_BIN repo create Bionic-AI-Solutions/FAISS-RAG \
    --public \
    --description "Enterprise Multi-Modal RAG System with FAISS vector search" \
    --source=. \
    --remote=origin \
    --push

echo ""
echo "✅ Repository created and code pushed successfully!"
echo "🔗 View at: https://github.com/Bionic-AI-Solutions/FAISS-RAG"


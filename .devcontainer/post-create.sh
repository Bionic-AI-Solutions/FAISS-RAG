#!/bin/bash

# Post-create script for devcontainer setup

echo "🚀 Setting up development environment..."

# Set up docker and kubectl symlinks
if [ -f /usr/bin/docker-host ]; then
    sudo ln -sf /usr/bin/docker-host /usr/bin/docker
    echo "✅ Docker CLI linked"
fi

if [ -f /usr/local/bin/kubectl-host ]; then
    sudo ln -sf /usr/local/bin/kubectl-host /usr/local/bin/kubectl
    echo "✅ kubectl linked"
fi

# Verify Docker access
if docker ps > /dev/null 2>&1; then
    echo "✅ Docker daemon accessible"
else
    echo "⚠️  Docker daemon not accessible (this is normal if Docker Desktop is not running)"
fi

# Verify kubectl access
if kubectl version --client > /dev/null 2>&1; then
    echo "✅ kubectl is working"
    kubectl cluster-info 2>/dev/null || echo "⚠️  Kubernetes cluster not accessible"
else
    echo "⚠️  kubectl not working"
fi

# Set up Python virtual environment (optional)
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Set up Node.js (if package.json exists)
if [ -f "package.json" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Set up Poetry (if pyproject.toml exists)
if [ -f "pyproject.toml" ]; then
    echo "📦 Installing Python dependencies with Poetry..."
    poetry install
fi

echo "✨ Development environment setup complete!"










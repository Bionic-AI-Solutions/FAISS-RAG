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

# Verify Docker group membership and fix if needed
echo "🔍 Checking Docker group configuration..."
DOCKER_GID=$(stat -c '%g' /var/run/docker.sock 2>/dev/null || echo "988")
CURRENT_DOCKER_GID=$(getent group docker 2>/dev/null | cut -d: -f3 || echo "")

if [ -n "$CURRENT_DOCKER_GID" ] && [ "$CURRENT_DOCKER_GID" != "$DOCKER_GID" ]; then
    echo "⚠️  Docker group GID mismatch (container: $CURRENT_DOCKER_GID, host: $DOCKER_GID)"
    echo "   Attempting to fix..."
    sudo groupmod -g "$DOCKER_GID" docker 2>/dev/null || \
        (sudo groupdel docker 2>/dev/null; sudo groupadd --gid "$DOCKER_GID" docker)
fi

# Ensure docker group exists with correct GID
if [ -z "$CURRENT_DOCKER_GID" ]; then
    echo "📦 Creating docker group with GID $DOCKER_GID..."
    sudo groupadd --gid "$DOCKER_GID" docker 2>/dev/null || true
fi

# Ensure user is in docker group
if ! groups | grep -q docker; then
    echo "⚠️  Adding user to docker group..."
    sudo usermod -aG docker $USER 2>/dev/null || true
    echo "ℹ️  Group membership updated. You may need to restart the container or run 'newgrp docker'"
fi

echo "✅ User groups: $(groups)"
echo "   Docker group GID: $(getent group docker | cut -d: -f3 2>/dev/null || echo 'not found')"
echo "   Socket GID: $DOCKER_GID"

# Verify Docker access
echo ""
echo "🔍 Testing Docker access..."
if docker ps > /dev/null 2>&1; then
    echo "✅ Docker daemon accessible"
    docker ps --format "table {{.Names}}\t{{.Status}}" | head -5
else
    echo "⚠️  Docker daemon not accessible"
    echo "   Docker socket info:"
    if [ -S /var/run/docker.sock ]; then
        ls -la /var/run/docker.sock
        echo ""
        echo "   Troubleshooting:"
        echo "   - Socket GID: $(stat -c '%g' /var/run/docker.sock)"
        echo "   - User GID: $(id -g)"
        echo "   - User groups: $(groups)"
        echo "   - Docker group GID: $(getent group docker | cut -d: -f3 2>/dev/null || echo 'not found')"
        echo ""
        echo "   If permission denied, try:"
        echo "   1. Restart the devcontainer"
        echo "   2. Or run: newgrp docker"
    else
        echo "   Docker socket not found at /var/run/docker.sock"
    fi
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










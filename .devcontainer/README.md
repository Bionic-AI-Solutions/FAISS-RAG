# DevContainer Setup

This devcontainer provides a complete development environment for Node.js and Python projects with Docker and Kubernetes support.

## Best Practices Applied

This devcontainer follows industry best practices:
- ✅ Docker build context set to `.devcontainer/` directory (not parent)
- ✅ Version-pinned dependencies for reproducibility
- ✅ `.dockerignore` file to optimize build performance
- ✅ No `--privileged` flag (using host Docker daemon instead)
- ✅ Security-focused configuration with read-only mounts

## Features

- **Python 3.11** with Poetry for dependency management
- **Node.js 20.x** with npm and common development tools
- **Docker CLI** - Uses host Docker daemon via socket mount
- **kubectl** - Mounted from host, configured with your Kubernetes cluster access
- **Development Tools**:
  - Python: black, flake8, pylint, pytest, pytest-asyncio, mypy
  - Node.js: TypeScript, ts-node, ESLint, Prettier, nodemon

## Prerequisites

- Docker Desktop or Docker Engine running on your host
- VS Code with the "Dev Containers" extension installed
- Docker socket accessible (default: `/var/run/docker.sock`)
- kubectl installed on host (default: `/usr/local/bin/kubectl`)
- Kubernetes config file at `~/.kube/config`

## What Gets Mounted

The devcontainer automatically mounts:

1. **Docker Socket** (`/var/run/docker.sock`) - Allows container to use host Docker daemon
2. **Docker CLI** (`/usr/bin/docker`) - Docker client from host
3. **kubectl** (`/usr/local/bin/kubectl`) - Kubernetes CLI from host
4. **Kubernetes Config** (`~/.kube`) - Your Kubernetes cluster configuration
5. **MCP Config** (`~/.cursor/mcp.json`) - MCP server configuration for Cursor

## Usage

1. Open the project in VS Code
2. When prompted, click "Reopen in Container" or use Command Palette: `Dev Containers: Reopen in Container`
3. Wait for the container to build and start (first time may take a few minutes)
4. The post-create script will automatically:
   - Set up Docker and kubectl symlinks
   - Verify Docker and Kubernetes access
   - Create Python virtual environment if needed
   - Install Node.js dependencies if `package.json` exists
   - Install Python dependencies with Poetry if `pyproject.toml` exists

## Verifying Setup

Once the container is running, verify everything works:

```bash
# Check Python
python3 --version  # Should show Python 3.11.13

# Check Node.js
node --version  # Should show v20.19.6

# Check Poetry
poetry --version  # Should show Poetry version

# Check Docker (uses host daemon)
docker ps

# Check kubectl
kubectl version --client
kubectl cluster-info  # Should show your cluster info
```

## Adding .cursorrules

If you have a `.cursorrules` file in your workspace root, you can add it to the mounts in `devcontainer.json`:

```json
"source=${localWorkspaceFolder}/.cursorrules,target=/workspace/.cursorrules,type=bind,readonly"
```

## Troubleshooting

### Docker not accessible
- Ensure Docker Desktop/Engine is running on your host
- Check that `/var/run/docker.sock` exists and is accessible

### kubectl not working
- Verify `~/.kube/config` exists on your host
- Check that kubectl is installed at `/usr/local/bin/kubectl` (or update the mount path)

### Permission issues

#### Docker Permission Denied
If you get `permission denied while trying to connect to the Docker daemon socket`:

1. **Check Docker group GID**: The container creates a docker group with GID 988 to match the host
2. **Verify group membership**: Run `groups` to see if you're in the docker group
3. **Restart container**: Group membership changes require a container restart
4. **Alternative**: Run `newgrp docker` in your terminal to activate group membership

The post-create script automatically:
- Creates docker group with GID matching the host (typically 988)
- Adds vscode user to the docker group
- Verifies Docker access

**Note**: The container runs as user `vscode` (UID 1000) and is automatically added to the docker group during setup.

## Customization

You can customize the devcontainer by:

- Modifying `.devcontainer/Dockerfile` to add additional tools
- Updating `.devcontainer/devcontainer.json` to change VS Code settings or extensions
- Editing `.devcontainer/post-create.sh` to add custom setup steps





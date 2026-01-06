#!/bin/bash
# Execute migrations by running Python in a container on the Docker network

set -e

echo "============================================================"
echo "Database Migration Execution"
echo "============================================================"
echo ""

# Check if Docker Compose is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi

# Check if services are running
if ! docker compose -f docker/docker-compose.yml ps postgres | grep -q "Up"; then
    echo "❌ PostgreSQL service is not running."
    echo "   Start services: docker compose -f docker/docker-compose.yml up -d"
    exit 1
fi

echo "✅ PostgreSQL service is running"
echo ""

# Get the absolute path to the workspace (use pwd for devcontainer compatibility)
WORKSPACE_PATH="$(cd /workspaces/mem0-rag 2>/dev/null && pwd || pwd)"

# Run migrations using a Python container on the same network
echo "🔄 Running migrations..."
docker run --rm \
    --network docker_mem0-rag-network \
    -v "${WORKSPACE_PATH}:/workspace" \
    -w /workspace \
    -e DB_HOST=postgres \
    -e DB_PORT=5432 \
    -e DB_NAME=mem0_rag_db \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres_password \
    python:3.11-slim \
    bash -c "
        pip install -q psycopg2-binary alembic sqlalchemy pydantic pydantic-settings > /dev/null 2>&1 && \
        python3 << 'PYTHON_SCRIPT'
import os
import sys
sys.path.insert(0, '/workspace')

from alembic import command
from alembic.config import Config

db_url = f\"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}\"

cfg = Config('/workspace/alembic.ini')
cfg.set_main_option('sqlalchemy.url', db_url)
cfg.set_main_option('script_location', '/workspace/app/db/migrations')

print('🔄 Running migrations...')
command.upgrade(cfg, 'head')
print('✅ Migrations completed successfully')
PYTHON_SCRIPT
    "

echo ""
echo "📊 Verifying tables created..."
docker compose -f docker/docker-compose.yml exec -T postgres \
    psql -U postgres -d mem0_rag_db -c "\dt"

echo ""
echo "✅ Migration execution complete!"


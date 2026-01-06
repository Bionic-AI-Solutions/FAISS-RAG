#!/bin/bash
# Run Alembic migrations using a temporary container with code mounted

set -e

echo "============================================================"
echo "Database Migration Script (Container-based)"
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

# Get database connection info from postgres container
DB_HOST=$(docker compose -f docker/docker-compose.yml exec -T postgres hostname -i | tr -d ' \n')
DB_PORT=5432
DB_NAME=mem0_rag_db
DB_USER=postgres
DB_PASSWORD=postgres_password

echo "📊 Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo ""

# Create a temporary Python script to run migrations
cat > /tmp/run_migrations_temp.py << 'PYTHON_SCRIPT'
import os
import sys
sys.path.insert(0, '/workspaces/mem0-rag')

from alembic import command
from alembic.config import Config

# Get database URL
db_host = os.environ.get('DB_HOST', 'postgres')
db_port = os.environ.get('DB_PORT', '5432')
db_name = os.environ.get('DB_NAME', 'mem0_rag_db')
db_user = os.environ.get('DB_USER', 'postgres')
db_password = os.environ.get('DB_PASSWORD', 'postgres_password')

db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Configure Alembic
alembic_cfg = Config('/workspaces/mem0-rag/alembic.ini')
alembic_cfg.set_main_option("sqlalchemy.url", db_url)

# Run migrations
print("🔄 Running migrations...")
command.upgrade(alembic_cfg, "head")
print("✅ Migrations completed successfully")
PYTHON_SCRIPT

# Run migrations using a Python container with code mounted
echo "🔄 Running migrations..."
docker run --rm \
    --network mem0-rag_mem0-rag-network \
    -v "$(pwd):/workspaces/mem0-rag" \
    -w /workspaces/mem0-rag \
    -e DB_HOST=postgres \
    -e DB_PORT=5432 \
    -e DB_NAME=mem0_rag_db \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres_password \
    python:3.11-slim \
    bash -c "
        pip install -q psycopg2-binary alembic sqlalchemy pydantic pydantic-settings > /dev/null 2>&1 && \
        python3 /tmp/run_migrations_temp.py
    "

# Cleanup
rm -f /tmp/run_migrations_temp.py

echo ""
echo "📊 Verifying tables created..."
docker compose -f docker/docker-compose.yml exec -T postgres \
    psql -U postgres -d mem0_rag_db -c "\dt"

echo ""
echo "✅ Migration execution complete!"


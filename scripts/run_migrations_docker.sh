#!/bin/bash
# Run Alembic migrations via Docker exec (when direct connection fails)

set -e

echo "============================================================"
echo "Database Migration Script (Docker Exec)"
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

# Run migrations via Docker exec
echo "🔄 Running migrations via Docker exec..."
docker compose -f docker/docker-compose.yml exec -T postgres \
    bash -c "cd /workspaces/mem0-rag && alembic upgrade head"

echo ""
echo "✅ Migrations completed successfully"
echo ""
echo "📊 Verifying tables created..."
docker compose -f docker/docker-compose.yml exec -T postgres \
    psql -U postgres -d mem0_rag_db -c "\dt"









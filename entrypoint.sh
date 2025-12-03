#!/bin/bash
set -e

# Função para aguardar o banco estar disponível
wait_for_db() {
    echo "Waiting for database to be ready..."
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if python -c "from app.database import engine; engine.connect()" 2>/dev/null; then
            echo "Database is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "Attempt $attempt/$max_attempts: Database not ready, waiting 2 seconds..."
        sleep 2
    done
    
    echo "ERROR: Database is not available after $max_attempts attempts"
    exit 1
}

# Verificar se DATABASE_URL está configurado
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

echo "DATABASE_URL is configured"

# Aguardar o banco estar disponível
wait_for_db

# Executar migrations
echo "Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migrations completed successfully"
else
    echo "ERROR: Migrations failed"
    exit 1
fi

# Iniciar aplicação
echo "Starting application..."
exec "$@"


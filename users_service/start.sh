#!/bin/sh

echo "Waiting for PostgreSQL..."

while ! nc -z db.microservices.svc.cluster.local 5432; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - checking for Vault secrets..."

# Le Vault Agent (sidecar) écrit ce fichier une fois le secret récupéré.
# On attend un court instant qu'il soit prêt, sans bloquer indéfiniment.
i=0
while [ ! -f /vault/secrets/database ] && [ "$i" -lt 10 ]; do
  echo "Waiting for Vault secret... ($i/10)"
  sleep 1
  i=$((i + 1))
done

if [ -f /vault/secrets/database ]; then
  echo "Vault secret found, loading..."
  . /vault/secrets/database
else
  echo "No Vault secret found, falling back to Kubernetes Secret env vars."
fi

echo "Starting app"

exec "$@"

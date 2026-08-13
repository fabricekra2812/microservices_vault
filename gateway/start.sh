#!/bin/sh

echo "Waiting for backend services..."

# On attend que users_service soit joignable
while ! nc -z users-service.microservices_vault.svc.cluster.local 8001; do
  echo "Waiting for users_service..."
  sleep 2
done

# On attend que products_service soit joignable
while ! nc -z products-service.microservices_vault.svc.cluster.local 8002; do
  echo "Waiting for products_service..."
  sleep 2
done

# On attend que orders_service soit joignable
while ! nc -z orders-service.microservices_vault.svc.cluster.local 8003; do
  echo "Waiting for orders_service..."
  sleep 2
done

echo "All backend services are up - starting gateway"

exec "$@"

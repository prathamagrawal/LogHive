#!/bin/bash

# Wait for RabbitMQ to be ready
until rabbitmqctl status; do
  echo "Waiting for RabbitMQ to start..."
  sleep 2
done

# Set permissions for buddy user
rabbitmqctl set_permissions -p / buddy ".*" ".*" ".*"

# Optional: Remove default guest user for security
rabbitmqctl delete_user guest || true
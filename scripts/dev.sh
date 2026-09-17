#!/usr/bin/env bash
set -e

echo "Starting EVENTRA development stack..."
docker-compose up -d postgres
echo "Postgres started."

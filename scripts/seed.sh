#!/usr/bin/env bash
set -e

echo "Seeding EVENTRA baseline data..."
cd apps/api
python -m app.seeds.seed_runner
echo "Database seeded successfully."

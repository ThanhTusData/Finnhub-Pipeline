#!/bin/bash
# Reset Spark Streaming checkpoint

set -e

CHECKPOINT_DIR=${1:-/tmp/checkpoint}

echo "⚠️  WARNING: This will delete all Spark checkpoint data!"
echo "Checkpoint directory: $CHECKPOINT_DIR"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo "Stopping Spark processor..."
    docker-compose stop spark-processor
    
    echo "Removing checkpoint data..."
    docker-compose exec spark-processor rm -rf $CHECKPOINT_DIR/*
    
    echo "Starting Spark processor..."
    docker-compose start spark-processor
    
    echo "✅ Checkpoint reset complete!"
else
    echo "❌ Operation cancelled"
fi
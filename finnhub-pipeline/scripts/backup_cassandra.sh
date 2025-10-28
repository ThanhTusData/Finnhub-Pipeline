#!/bin/bash
# Backup Cassandra data

set -e

BACKUP_DIR=${1:-./backups}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
KEYSPACE="trading"

echo "🗄️  Starting Cassandra backup..."
echo "Keyspace: $KEYSPACE"
echo "Backup directory: $BACKUP_DIR"

# Create backup directory
mkdir -p $BACKUP_DIR

# Export schema
echo "Exporting schema..."
docker exec cassandra cqlsh -e "DESC KEYSPACE $KEYSPACE" > $BACKUP_DIR/schema_$TIMESTAMP.cql

# Backup data using nodetool snapshot
echo "Creating snapshot..."
docker exec cassandra nodetool snapshot -t backup_$TIMESTAMP $KEYSPACE

# Copy snapshot data
echo "Copying snapshot data..."
docker cp cassandra:/var/lib/cassandra/data/$KEYSPACE $BACKUP_DIR/data_$TIMESTAMP

echo "✅ Backup complete!"
echo "Files saved to: $BACKUP_DIR"
echo "  - schema_$TIMESTAMP.cql"
echo "  - data_$TIMESTAMP/"
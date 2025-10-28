#!/bin/bash
# Check Kafka consumer lag

KAFKA_CONTAINER="kafka"
BOOTSTRAP_SERVER="localhost:9092"
GROUP_ID=${1:-spark-streaming}

echo "📊 Checking Kafka consumer lag for group: $GROUP_ID"
echo "================================================"

docker exec $KAFKA_CONTAINER kafka-consumer-groups \
    --bootstrap-server $BOOTSTRAP_SERVER \
    --describe \
    --group $GROUP_ID

echo ""
echo "Legend:"
echo "  LAG: Number of messages behind"
echo "  CURRENT-OFFSET: Current position in topic"
echo "  LOG-END-OFFSET: Latest message in topic"
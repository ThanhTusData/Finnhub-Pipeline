# Schema Registry

Avro schemas for the trading pipeline messages.

## Overview

This directory contains Avro schema definitions for all messages flowing through the pipeline. Using a schema registry ensures:

- **Type Safety**: Enforced data types and structure
- **Evolution**: Backward/forward compatible schema changes
- **Documentation**: Self-documenting data formats
- **Validation**: Automatic validation at producer/consumer

## Schemas

### market-value.avsc (v1)
Base schema for stock trade data.

**Fields**:
- `symbol`: Stock ticker symbol
- `price`: Trade price
- `timestamp`: Trade time (ms since epoch)
- `volume`: Number of shares
- `conditions`: Trade condition codes
- `processed_at`: Processing timestamp

**Usage**:
```python
from confluent_kafka import avro

schema = avro.load('schemas/market-value.avsc')
producer = AvroProducer({
    'bootstrap.servers': 'kafka:9092',
    'schema.registry.url': 'http://schema-registry:8081'
}, default_value_schema=schema)
```

### market-value-v2.avsc (v2)
Enhanced schema with additional fields.

**New Fields**:
- `exchange`: Exchange code
- `trade_id`: Unique identifier
- `bid_price`: Best bid at trade time
- `ask_price`: Best ask at trade time
- `is_market_hours`: Market hours flag
- `metadata`: Extensible metadata map

**Migration**:
All new fields are optional (nullable with defaults) for backward compatibility.

### dlq-message.avsc
Dead Letter Queue schema for failed messages.

**Purpose**:
- Capture failed processing attempts
- Store original message and error details
- Enable debugging and retry logic

## Schema Evolution

### Compatibility Types

**Backward Compatible** (Recommended):
- Add optional fields (with defaults)
- Remove optional fields

**Forward Compatible**:
- Add new fields (consumers ignore unknown fields)
- Remove fields (producers skip missing fields)

**Full Compatible**:
- Both backward and forward compatible

### Version Strategy

- **Major Version**: Breaking changes (e.g., v1 → v2)
- **Minor Version**: Backward-compatible additions
- **Patch Version**: Documentation/metadata only

### Example Evolution

```json
// v1: Original
{"name": "symbol", "type": "string"}

// v2: Add optional field (backward compatible)
{"name": "exchange", "type": ["null", "string"], "default": null}

// v3: BREAKING - remove field (not compatible)
// Don't do this! Instead, deprecate and add new field
```

## Setup Schema Registry

### Docker Compose
```yaml
schema-registry:
  image: confluentinc/cp-schema-registry:7.5.0
  ports:
    - "8081:8081"
  environment:
    SCHEMA_REGISTRY_HOST_NAME: schema-registry
    SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: kafka:9092
```

### Register Schemas
```bash
# Register market-value schema
curl -X POST http://localhost:8081/subjects/stock-trades-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data @schemas/market-value.avsc

# List subjects
curl http://localhost:8081/subjects

# Get schema versions
curl http://localhost:8081/subjects/stock-trades-value/versions
```

## Validation

### Python Validation
```python
import avro.schema
from avro.io import DatumWriter, BinaryEncoder
import io

# Load schema
schema = avro.schema.parse(open('schemas/market-value.avsc').read())

# Validate data
data = {
    "symbol": "AAPL",
    "price": 150.25,
    "timestamp": 1635724800000,
    "volume": 100.0,
    "conditions": [],
    "processed_at": 1635724800500
}

# This will raise exception if data doesn't match schema
writer = DatumWriter(schema)
bytes_writer = io.BytesIO()
encoder = BinaryEncoder(bytes_writer)
writer.write(data, encoder)
```

### Java Validation
```java
Schema schema = new Schema.Parser().parse(
    new File("schemas/market-value.avsc")
);

GenericRecord record = new GenericData.Record(schema);
record.put("symbol", "AAPL");
record.put("price", 150.25);
// ... set other fields

// Validate
GenericDatumWriter writer = 
    new GenericDatumWriter<>(schema);
```

## Best Practices

1. **Always use schema registry in production**
   - Prevents data inconsistencies
   - Enables safe evolution

2. **Document all fields**
   - Include `doc` attribute
   - Explain purpose and constraints

3. **Use logical types**
   - `timestamp-millis` for timestamps
   - `decimal` for precise numbers

4. **Default values for new fields**
   - Ensures backward compatibility
   - Use `null` or appropriate default

5. **Test schema evolution**
   - Validate old consumers work with new schema
   - Test new consumers with old data

6. **Version control schemas**
   - Track changes in git
   - Use semantic versioning

## Roadmap

- [ ] Add Schema Registry to docker-compose
- [ ] Implement Avro serialization in producer
- [ ] Add schema validation in Spark
- [ ] Create schema evolution tests
- [ ] Add protobuf schema support
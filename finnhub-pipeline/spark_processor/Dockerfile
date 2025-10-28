FROM bitnami/spark:3.5.0

USER root

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy Spark configuration
COPY spark-defaults.conf /opt/bitnami/spark/conf/

# Set permissions
RUN chown -R 1001:1001 /app

USER 1001

CMD ["/opt/bitnami/spark/bin/spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1", \
     "--master", "local[*]", \
     "src/stream_processor.py"]
FROM bitnami/spark:3.4.1

USER root

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app/
WORKDIR /app

CMD ["python", "stream_processor.py"]
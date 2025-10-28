FROM grafana/grafana:10.0.0

# Cài plugin Cassandra datasource
RUN grafana-cli plugins install hadesarchitect-cassandra-datasource

# (Tùy chọn) Cho phép plugin chưa ký
ENV GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=hadesarchitect-cassandra-datasource

# Kubernetes Deployment

Production-ready Kubernetes manifests for the trading pipeline.

## Structure

```
kubernetes/
├── base/                          # Base configurations
│   ├── namespace.yaml
│   ├── kafka/                     # Kafka StatefulSet
│   ├── cassandra/                 # Cassandra StatefulSet
│   ├── spark/                     # Spark Deployment
│   └── observability/             # Prometheus, Grafana
│
└── overlays/                      # Environment-specific configs
    ├── dev/                       # Development
    ├── staging/                   # Staging
    └── production/                # Production
```

## Environments

### Development
- **Namespace**: `trading-pipeline-dev`
- **Replicas**: 1 for all services
- **Resources**: Minimal (2-4Gi RAM, 1 CPU)
- **Storage**: 10Gi volumes
- **Purpose**: Local development and testing

### Staging
- **Namespace**: `trading-pipeline-staging`
- **Replicas**: 2-3 per service
- **Resources**: Moderate (6-12Gi RAM, 2-4 CPU)
- **Storage**: 50-200Gi volumes
- **Purpose**: Pre-production testing

### Production
- **Namespace**: `trading-pipeline`
- **Replicas**: 3-5 per service
- **Resources**: High (16-32Gi RAM, 8-16 CPU)
- **Storage**: 100-500Gi volumes
- **Purpose**: Production workloads

## Deployment

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install kustomize
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash

# Verify cluster connection
kubectl cluster-info
```

### Deploy to Development

```bash
# Apply development configuration
kubectl apply -k overlays/dev/

# Verify deployment
kubectl get pods -n trading-pipeline-dev

# Check services
kubectl get svc -n trading-pipeline-dev

# View logs
kubectl logs -f -n trading-pipeline-dev deployment/dev-finnhub-producer
```

### Deploy to Staging

```bash
# Apply staging configuration
kubectl apply -k overlays/staging/

# Verify deployment
kubectl get pods -n trading-pipeline-staging

# Port forward Grafana
kubectl port-forward -n trading-pipeline-staging svc/staging-grafana 3000:3000
```

### Deploy to Production

```bash
# Apply production configuration
kubectl apply -k overlays/production/

# Verify all pods are running
kubectl get pods -n trading-pipeline

# Check StatefulSet status
kubectl get statefulset -n trading-pipeline

# Monitor rollout
kubectl rollout status -n trading-pipeline deployment/finnhub-producer
```

## Scaling

### Horizontal Scaling

```bash
# Scale producers
kubectl scale deployment finnhub-producer -n trading-pipeline --replicas=5

# Scale Spark processors
kubectl scale deployment spark-processor -n trading-pipeline --replicas=4

# Scale Kafka (StatefulSet)
kubectl scale statefulset kafka -n trading-pipeline --replicas=5
```

### Vertical Scaling

Edit resource limits in overlay kustomization.yaml:

```yaml
patches:
- target:
    kind: Deployment
    name: spark-processor
  patch: |-
    - op: replace
      path: /spec/template/spec/containers/0/resources/limits/memory
      value: "32Gi"
```

Then apply:
```bash
kubectl apply -k overlays/production/
```

## Monitoring

### Check Pod Status

```bash
# All pods
kubectl get pods -n trading-pipeline

# Specific service
kubectl get pods -n trading-pipeline -l app=kafka

# Pod details
kubectl describe pod -n trading-pipeline kafka-0
```

### View Logs

```bash
# Producer logs
kubectl logs -f -n trading-pipeline deployment/finnhub-producer

# Spark logs
kubectl logs -f -n trading-pipeline deployment/spark-processor

# Kafka logs
kubectl logs -f -n trading-pipeline kafka-0

# Cassandra logs
kubectl logs -f -n trading-pipeline cassandra-0
```

### Access Services

```bash
# Port forward Grafana
kubectl port-forward -n trading-pipeline svc/grafana 3000:3000

# Port forward Prometheus
kubectl port-forward -n trading-pipeline svc/prometheus 9090:9090

# Port forward Kafka (for debugging)
kubectl port-forward -n trading-pipeline kafka-0 9092:9092
```

## Storage Management

### Check PVCs

```bash
# List persistent volume claims
kubectl get pvc -n trading-pipeline

# Describe PVC
kubectl describe pvc kafka-data-kafka-0 -n trading-pipeline
```

### Backup Volumes

```bash
# Create snapshot (if supported by storage class)
kubectl create -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: cassandra-snapshot-$(date +%Y%m%d)
  namespace: trading-pipeline
spec:
  source:
    persistentVolumeClaimName: cassandra-data-cassandra-0
EOF
```

## Troubleshooting

### Pod Not Starting

```bash
# Check events
kubectl get events -n trading-pipeline --sort-by='.lastTimestamp'

# Check pod status
kubectl describe pod  -n trading-pipeline

# Check logs
kubectl logs  -n trading-pipeline --previous
```

### StatefulSet Issues

```bash
# Check StatefulSet status
kubectl get statefulset -n trading-pipeline

# Describe StatefulSet
kubectl describe statefulset kafka -n trading-pipeline

# Delete and recreate pod
kubectl delete pod kafka-0 -n trading-pipeline
```

### Network Issues

```bash
# Test connectivity from producer to Kafka
kubectl exec -it -n trading-pipeline deployment/finnhub-producer -- nc -zv kafka 9092

# Test Cassandra connectivity
kubectl exec -it -n trading-pipeline deployment/spark-processor -- nc -zv cassandra 9042

# Check network policies
kubectl get networkpolicy -n trading-pipeline
```

### Resource Issues

```bash
# Check resource usage
kubectl top pods -n trading-pipeline
kubectl top nodes

# Check resource quotas
kubectl get resourcequota -n trading-pipeline

# Describe resource limits
kubectl describe limitrange -n trading-pipeline
```

## Updates & Rollback

### Update Image

```bash
# Update producer image
kubectl set image deployment/finnhub-producer \
  finnhub-producer=finnhub-producer:v2.0.0 \
  -n trading-pipeline

# Check rollout status
kubectl rollout status deployment/finnhub-producer -n trading-pipeline
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/finnhub-producer -n trading-pipeline

# Rollback to specific revision
kubectl rollout undo deployment/finnhub-producer --to-revision=2 -n trading-pipeline

# Check rollout history
kubectl rollout history deployment/finnhub-producer -n trading-pipeline
```

## Clean Up

### Delete Environment

```bash
# Delete development
kubectl delete -k overlays/dev/

# Delete staging
kubectl delete -k overlays/staging/

# Delete production (CAUTION!)
kubectl delete -k overlays/production/
```

### Delete Specific Resources

```bash
# Delete deployment
kubectl delete deployment finnhub-producer -n trading-pipeline

# Delete service
kubectl delete service kafka -n trading-pipeline

# Delete namespace (deletes everything in it)
kubectl delete namespace trading-pipeline
```

## Best Practices

1. **Use Kustomize** for environment-specific configs
2. **Set resource limits** for all containers
3. **Use PodDisruptionBudgets** for high availability
4. **Enable monitoring** with Prometheus ServiceMonitors
5. **Configure health checks** (liveness/readiness probes)
6. **Use NetworkPolicies** to restrict traffic
7. **Enable RBAC** for security
8. **Regular backups** of persistent volumes
9. **Use Horizontal Pod Autoscaler** for dynamic scaling
10. **Monitor resource usage** and adjust limits

## Security

### RBAC

```bash
# Create service account
kubectl create serviceaccount trading-pipeline -n trading-pipeline

# Create role
kubectl create role pod-reader \
  --verb=get,list,watch \
  --resource=pods \
  -n trading-pipeline

# Create role binding
kubectl create rolebinding pod-reader-binding \
  --role=pod-reader \
  --serviceaccount=trading-pipeline:trading-pipeline \
  -n trading-pipeline
```

### Secrets Management

```bash
# Create secret from file
kubectl create secret generic finnhub-api-key \
  --from-file=api-key=./secret.txt \
  -n trading-pipeline

# Create TLS secret
kubectl create secret tls trading-pipeline-tls \
  --cert=./cert.pem \
  --key=./key.pem \
  -n trading-pipeline
```

## Support

For issues or questions:
1. Check logs: `kubectl logs`
2. Check events: `kubectl get events`
3. Review documentation in `/docs`
4. Open GitHub issue with details
# Enterprise Multi-Modal RAG System - Operations Manual

## Version: 1.0
## Last Updated: 2025-12-26

---

## Table of Contents

1. [Operational Overview](#operational-overview)
2. [Monitoring & Alerting](#monitoring--alerting)
3. [Backup & Recovery](#backup--recovery)
4. [Incident Response](#incident-response)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Capacity Planning](#capacity-planning)

---

## 1. Operational Overview

### 1.1 Service Level Objectives (SLOs)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Availability | 99.95% | Monthly uptime |
| Query Latency (p95) | < 800ms | Per-query measurement |
| Query Latency (p99) | < 1.5s | Per-query measurement |
| Error Rate | < 0.1% | Errors / total requests |
| Document Processing | > 1,000 docs/sec | Ingestion throughput |

### 1.2 On-Call Rotation

**Primary On-Call:** Platform Engineer
**Secondary On-Call:** Backend Engineer
**Escalation:** Technical Lead

**Shift Schedule:**
- Week 1: Engineer A (primary), Engineer B (secondary)
- Week 2: Engineer B (primary), Engineer C (secondary)
- Week 3: Engineer C (primary), Engineer A (secondary)

**On-Call Responsibilities:**
- Respond to critical alerts within 15 minutes
- Resolve P1 incidents within 2 hours
- Document all incidents
- Perform root cause analysis
- Update runbooks

### 1.3 Communication Channels

- **Incidents:** PagerDuty → Slack #incidents
- **Alerts:** Prometheus → Slack #alerts
- **Status Page:** status.rag-system.com
- **Internal:** Slack #rag-ops
- **Escalation:** Direct phone contact

---

## 2. Monitoring & Alerting

### 2.1 Monitoring Stack

**Components:**
- Prometheus: Metrics collection
- Grafana: Visualization
- Jaeger: Distributed tracing
- ELK: Log aggregation
- AlertManager: Alert routing

### 2.2 Key Dashboards

#### System Overview Dashboard

```
URL: https://grafana.rag-system.com/d/system-overview

Panels:
1. Cluster Health
   - Node status
   - Pod health
   - Resource utilization

2. Service Status
   - Query service health
   - Ingestion worker health
   - Data store health

3. Performance Metrics
   - Request rate
   - Latency (p50, p95, p99)
   - Error rate

4. Resource Usage
   - CPU utilization
   - Memory usage
   - Disk IOPS
   - Network throughput
```

#### Query Service Dashboard

```
URL: https://grafana.rag-system.com/d/query-service

Panels:
1. Request Metrics
   - Queries per second
   - Response times
   - Success vs error rates

2. Cache Performance
   - Hit rate
   - Miss rate
   - Cache size

3. LLM Usage
   - Requests per provider
   - Token usage
   - Cost tracking

4. Retrieval Performance
   - FAISS search latency
   - ES search latency
   - Neo4j query latency
```

#### Data Store Dashboard

```
URL: https://grafana.rag-system.com/d/datastores

Panels:
1. Redis
   - Operations per second
   - Memory usage
   - Evictions
   - Replication lag

2. PostgreSQL
   - Active connections
   - Query performance
   - Replication lag
   - Table sizes

3. Elasticsearch
   - Indexing rate
   - Search rate
   - Cluster health
   - Shard status

4. FAISS
   - Index size
   - Search latency
   - Memory usage
```

### 2.3 Alert Configuration

#### Critical Alerts (P1)

```yaml
# High error rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
  for: 5m
  labels:
    severity: critical
    component: query-service
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }}% over last 5 minutes"

# API latency exceeds SLO
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.8
  for: 5m
  labels:
    severity: critical
    component: query-service
  annotations:
    summary: "API latency exceeds SLO"
    description: "p95 latency is {{ $value }}s"

# Service down
- alert: ServiceDown
  expr: up{job="query-service"} == 0
  for: 2m
  labels:
    severity: critical
    component: query-service
  annotations:
    summary: "Query service is down"
    description: "Query service has been down for 2 minutes"

# Database down
- alert: DatabaseDown
  expr: up{job="postgres"} == 0
  for: 1m
  labels:
    severity: critical
    component: postgres
  annotations:
    summary: "PostgreSQL is down"
    description: "Database is unavailable"

# Disk space critical
- alert: DiskSpaceCritical
  expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Disk space critical"
    description: "Less than 10% disk space available on {{ $labels.instance }}"
```

#### Warning Alerts (P2)

```yaml
# Cache hit rate low
- alert: LowCacheHitRate
  expr: rate(cache_hits_total[10m]) / rate(cache_requests_total[10m]) < 0.7
  for: 15m
  labels:
    severity: warning
    component: redis
  annotations:
    summary: "Cache hit rate below 70%"
    description: "Current hit rate: {{ $value }}%"

# High memory usage
- alert: HighMemoryUsage
  expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.2
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High memory usage"
    description: "Less than 20% memory available"

# Pod restart loop
- alert: PodRestartLoop
  expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Pod restarting frequently"
    description: "Pod {{ $labels.pod }} is restarting"
```

### 2.4 Alert Response Procedures

#### P1 Alert Response (Critical)

```
1. Acknowledge alert in PagerDuty (< 5 minutes)
2. Join incident Slack channel
3. Assess impact:
   - Check affected services
   - Estimate user impact
   - Review recent changes
4. Implement immediate mitigation:
   - Rollback if recent deployment
   - Scale resources if capacity issue
   - Fail over if database issue
5. Communicate:
   - Update status page
   - Notify stakeholders
   - Post to #incidents channel
6. Resolve issue
7. Post-incident review within 48 hours
```

#### P2 Alert Response (Warning)

```
1. Acknowledge alert
2. Investigate root cause
3. Schedule fix if non-urgent
4. Document findings
5. Update monitoring if needed
```

---

## 3. Backup & Recovery

### 3.1 Backup Strategy

#### PostgreSQL Backups

```bash
# Full backup (daily at 1 AM)
0 1 * * * /scripts/postgres-backup.sh full

# Incremental backup (hourly)
0 * * * * /scripts/postgres-backup.sh incremental

# Backup script
#!/bin/bash
BACKUP_TYPE=$1
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups/postgres

if [ "$BACKUP_TYPE" == "full" ]; then
    pg_dump -U rag_admin rag_system | gzip > $BACKUP_DIR/full_$DATE.sql.gz
else
    # WAL archiving for incremental
    pg_receivewal -D $BACKUP_DIR/wal -S replication_slot
fi

# Upload to S3
aws s3 cp $BACKUP_DIR s3://rag-backups/postgres/ --recursive

# Retention: 7 days full, 24 hours incremental
find $BACKUP_DIR/full_* -mtime +7 -delete
find $BACKUP_DIR/wal/ -mtime +1 -delete
```

#### FAISS Index Backups

```bash
# Daily index snapshots
0 2 * * * /scripts/faiss-backup.sh

# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR=/backups/faiss

# For each tenant index
for tenant_dir in /data/faiss/*/; do
    tenant_id=$(basename $tenant_dir)
    
    # Create snapshot
    tar -czf $BACKUP_DIR/faiss_${tenant_id}_${DATE}.tar.gz $tenant_dir
    
    # Upload to S3
    aws s3 cp $BACKUP_DIR/faiss_${tenant_id}_${DATE}.tar.gz \
        s3://rag-backups/faiss/
done

# Retention: 30 days
find $BACKUP_DIR -mtime +30 -delete
```

#### Redis Backups

```bash
# RDB snapshots (every 6 hours)
# Configured in redis.conf:
save 21600 1

# Manual backup trigger
redis-cli BGSAVE

# Backup location: /data/dump.rdb
# Copied to S3 hourly via cron:
0 * * * * aws s3 cp /data/redis/dump.rdb s3://rag-backups/redis/dump_$(date +%Y%m%d_%H).rdb
```

#### Elasticsearch Snapshots

```bash
# Configure snapshot repository
PUT /_snapshot/s3_repository
{
  "type": "s3",
  "settings": {
    "bucket": "rag-backups",
    "region": "us-west-2",
    "base_path": "elasticsearch"
  }
}

# Daily snapshots
PUT /_snapshot/s3_repository/snapshot_$(date +%Y%m%d)
{
  "indices": "documents_*",
  "include_global_state": false
}

# Retention: 14 days
```

### 3.2 Recovery Procedures

#### PostgreSQL Recovery

```bash
# Full restore
#!/bin/bash

# Stop application services
kubectl scale deployment query-service --replicas=0 -n rag-system

# Restore from backup
BACKUP_FILE=full_20251226_010000.sql.gz
gunzip -c $BACKUP_FILE | psql -U rag_admin rag_system

# If point-in-time recovery needed:
# 1. Restore base backup
# 2. Apply WAL logs
pg_waldump /backups/postgres/wal/*.wal | psql -U rag_admin rag_system

# Restart services
kubectl scale deployment query-service --replicas=10 -n rag-system

# Verify data integrity
psql -U rag_admin -d rag_system -c "SELECT COUNT(*) FROM metadata.documents;"
```

#### FAISS Index Recovery

```bash
#!/bin/bash

TENANT_ID=$1
BACKUP_DATE=$2

# Stop services accessing this index
kubectl scale deployment query-service --replicas=0 -n rag-system

# Download and extract backup
aws s3 cp s3://rag-backups/faiss/faiss_${TENANT_ID}_${BACKUP_DATE}.tar.gz .
tar -xzf faiss_${TENANT_ID}_${BACKUP_DATE}.tar.gz -C /data/faiss/

# Restart services
kubectl scale deployment query-service --replicas=10 -n rag-system

# Verify index
python3 verify_index.py --tenant-id $TENANT_ID
```

#### Redis Recovery

```bash
#!/bin/bash

# Stop Redis
kubectl scale statefulset redis-cluster --replicas=0 -n rag-system

# Restore RDB file
BACKUP_FILE=dump_20251226_10.rdb
aws s3 cp s3://rag-backups/redis/$BACKUP_FILE /data/redis/dump.rdb

# Start Redis
kubectl scale statefulset redis-cluster --replicas=6 -n rag-system

# Verify data
redis-cli DBSIZE
```

### 3.3 Disaster Recovery

#### Complete Cluster Failure

```
RTO: 4 hours
RPO: 1 hour

Recovery Steps:

1. Provision new cluster
   - Deploy Kubernetes
   - Configure storage
   - Set up networking

2. Restore infrastructure services
   - Deploy Vault
   - Deploy secrets
   - Deploy monitoring

3. Restore data stores (parallel)
   - PostgreSQL: Latest full + incremental backups
   - Redis: Latest RDB snapshot
   - Elasticsearch: Latest snapshot
   - FAISS: Latest index backups
   - MinIO: Cross-region replication

4. Deploy application services
   - Query service
   - Ingestion workers
   - API gateway

5. Verify functionality
   - Run smoke tests
   - Check monitoring
   - Validate data integrity

6. Switch traffic to new cluster
   - Update DNS
   - Monitor for issues
```

#### Data Center Outage

```
RTO: 30 minutes
RPO: 5 minutes

Recovery Steps:

1. Automatic failover to secondary region
   - Traffic manager redirects requests
   - Database replicas promoted

2. Verify service health
   - Check all pods running
   - Verify data consistency

3. Monitor performance
   - Ensure SLOs met
   - Scale if needed
```

---

## 4. Incident Response

### 4.1 Incident Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P1 | Critical | 15 min | Complete outage, data loss |
| P2 | High | 1 hour | Degraded performance, partial outage |
| P3 | Medium | 4 hours | Minor issues, workaround available |
| P4 | Low | 24 hours | Cosmetic issues, feature requests |

### 4.2 Incident Response Process

```
1. Detection & Alert
   ├─ Automated alert fired
   ├─ On-call engineer paged
   └─ Incident slack channel created

2. Assessment (< 5 minutes)
   ├─ Determine severity
   ├─ Identify affected services
   ├─ Estimate user impact
   └─ Page additional team members if P1

3. Communication
   ├─ Update status page
   ├─ Post in #incidents channel
   ├─ Notify stakeholders
   └─ Set up war room if needed

4. Mitigation
   ├─ Implement immediate fix
   ├─ Rollback if needed
   ├─ Scale resources
   └─ Document actions taken

5. Resolution
   ├─ Verify issue resolved
   ├─ Monitor for recurrence
   ├─ Update status page
   └─ Close incident

6. Post-Incident Review (< 48 hours)
   ├─ Write incident report
   ├─ Root cause analysis
   ├─ Action items for prevention
   └─ Update runbooks
```

### 4.3 Common Incidents & Runbooks

#### High Query Latency

```
Symptoms:
- p95 latency > 1s
- User complaints about slow responses

Investigation:
1. Check Query Service Dashboard
   - Request rate spike?
   - Cache hit rate drop?
   - LLM provider latency?

2. Check Data Store Performance
   - FAISS search latency?
   - ES query performance?
   - PostgreSQL slow queries?

3. Check Resource Usage
   - CPU saturation?
   - Memory pressure?
   - Disk I/O?

Mitigation:
1. Scale query service pods
   kubectl scale deployment query-service --replicas=50 -n rag-system

2. Warm cache if hit rate low
   python3 cache_warmer.py --top-queries 1000

3. Optimize FAISS search
   # Reduce nprobe temporarily
   Update FAISS config: nprobe=32

4. If LLM provider slow, switch provider
   # Route to alternative provider
   Update routing config

Resolution:
1. Identify root cause
2. Implement permanent fix
3. Monitor for 24 hours
```

#### Database Connection Exhaustion

```
Symptoms:
- "too many connections" errors
- Unable to process queries

Investigation:
1. Check active connections
   SELECT count(*) FROM pg_stat_activity;

2. Check for long-running queries
   SELECT pid, now() - query_start as duration, query 
   FROM pg_stat_activity 
   WHERE state = 'active' 
   ORDER BY duration DESC;

Mitigation:
1. Increase max_connections (temporary)
   ALTER SYSTEM SET max_connections = 2000;
   SELECT pg_reload_conf();

2. Kill long-running queries
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE query_start < now() - interval '10 minutes';

3. Scale connection pooling
   kubectl scale deployment pgbouncer --replicas=5

Resolution:
1. Optimize application connection management
2. Implement connection pooling
3. Right-size max_connections
```

#### Disk Space Critical

```
Symptoms:
- Disk usage > 90%
- Write errors

Investigation:
1. Identify large directories
   du -sh /* | sort -h

2. Check for log buildup
   du -sh /var/log/*

3. Check old backups
   du -sh /backups/*

Mitigation:
1. Clean old logs
   find /var/log -name "*.log" -mtime +7 -delete

2. Remove old backups
   find /backups -mtime +30 -delete

3. Expand storage (if available)
   kubectl patch pvc postgres-data -p '{"spec":{"resources":{"requests":{"storage":"2Ti"}}}}'

Resolution:
1. Implement log rotation
2. Automate backup cleanup
3. Set up disk usage alerts at 80%
```

---

## 5. Maintenance Procedures

### 5.1 Regular Maintenance Schedule

| Task | Frequency | Day/Time | Owner |
|------|-----------|----------|-------|
| Security patches | Weekly | Sunday 2 AM | Platform |
| Database maintenance | Weekly | Sunday 3 AM | Backend |
| Index optimization | Monthly | 1st Sunday 2 AM | ML |
| Backup verification | Monthly | 15th of month | Platform |
| Certificate renewal | Quarterly | As needed | Security |
| Capacity review | Monthly | Last Friday | Platform |

### 5.2 Update Procedures

#### Application Updates

```bash
# Blue-Green Deployment Process

1. Deploy to green environment
   kubectl apply -f deployment-green.yaml -n rag-system

2. Wait for pods to be ready
   kubectl wait --for=condition=ready pod -l app=query-service-green -n rag-system

3. Run smoke tests
   ./smoke-tests.sh --env green

4. Split traffic (10% to green)
   kubectl apply -f traffic-split-10.yaml

5. Monitor for 30 minutes
   # Watch error rates and latency

6. Increase traffic gradually (50%, then 100%)
   kubectl apply -f traffic-split-50.yaml
   # Wait 30 minutes, monitor
   kubectl apply -f traffic-split-100.yaml

7. If successful, update blue to new version
   kubectl apply -f deployment-blue.yaml -n rag-system

8. Rollback procedure (if issues)
   kubectl apply -f traffic-split-0.yaml  # Route all to blue
   kubectl delete deployment query-service-green
```

#### Database Schema Updates

```bash
# Safe Schema Migration Process

1. Take backup
   pg_dump -U rag_admin rag_system > backup_pre_migration.sql

2. Test migration on replica
   psql -U rag_admin -h replica rag_system < migration.sql

3. Put application in maintenance mode (if needed)
   kubectl scale deployment query-service --replicas=0

4. Run migration
   psql -U rag_admin rag_system < migration.sql

5. Verify migration
   psql -U rag_admin -d rag_system -c "\d+ table_name"

6. Restart application
   kubectl scale deployment query-service --replicas=10

7. Monitor for issues

8. Rollback procedure (if issues)
   psql -U rag_admin rag_system < rollback.sql
```

#### Kubernetes Cluster Upgrades

```bash
# Cluster Upgrade Process

1. Review upgrade notes
   # Check Kubernetes changelog for breaking changes

2. Upgrade control plane
   kubeadm upgrade plan
   kubeadm upgrade apply v1.28.0

3. Upgrade worker nodes (one at a time)
   # Drain node
   kubectl drain node-1 --ignore-daemonsets --delete-emptydir-data
   
   # Upgrade node
   ssh node-1
   sudo kubeadm upgrade node
   sudo systemctl restart kubelet
   
   # Uncordon node
   kubectl uncordon node-1
   
   # Wait for node to be ready
   kubectl wait --for=condition=ready node node-1

4. Verify cluster health
   kubectl get nodes
   kubectl get pods --all-namespaces

5. Run smoke tests
   ./smoke-tests.sh
```

### 5.3 Scaling Procedures

#### Horizontal Scaling

```bash
# Scale query service
kubectl scale deployment query-service --replicas=20 -n rag-system

# Scale ingestion workers
kubectl scale deployment ingestion-worker --replicas=50 -n rag-ingestion

# Update HPA limits
kubectl patch hpa query-service-hpa -n rag-system -p '{"spec":{"maxReplicas":1000}}'
```

#### Vertical Scaling

```bash
# Increase resources for query service
kubectl set resources deployment query-service \
  --requests=cpu=4000m,memory=8Gi \
  --limits=cpu=8000m,memory=16Gi \
  -n rag-system

# Restart pods for new resources
kubectl rollout restart deployment query-service -n rag-system
```

#### Add FAISS Shard

```bash
# When index exceeds 10M vectors

1. Create new shard
   python3 create_shard.py --tenant-id $TENANT_ID --shard-id $NEW_SHARD

2. Redistribute vectors
   python3 redistribute.py --tenant-id $TENANT_ID

3. Update query routing
   # Configure IndexShards to include new shard

4. Verify search functionality
   python3 test_search.py --tenant-id $TENANT_ID
```

---

## 6. Troubleshooting Guide

### 6.1 Common Issues

#### Pod Crash Loops

```
Symptoms:
- Pod repeatedly restarting
- CrashLoopBackOff status

Diagnosis:
kubectl describe pod <pod-name> -n rag-system
kubectl logs <pod-name> -n rag-system --previous

Common Causes:
1. OOM (Out of Memory)
   - Check memory limits
   - Look for memory leaks

2. Application error
   - Check logs for exceptions
   - Verify configuration

3. Dependency unavailable
   - Check if database/cache accessible
   - Verify service endpoints

Resolution:
# Increase resources
kubectl set resources deployment <name> --limits=memory=4Gi

# Fix configuration
kubectl edit deployment <name> -n rag-system

# Check dependencies
kubectl exec -it <pod> -- curl http://postgres:5432
```

#### Redis Connection Failures

```
Symptoms:
- Connection timeout errors
- Session data lost

Diagnosis:
kubectl exec -n rag-system redis-cluster-0 -- redis-cli cluster info
kubectl logs -n rag-system redis-cluster-0

Common Causes:
1. Cluster split-brain
2. Node failures
3. Network partition

Resolution:
# Check cluster state
kubectl exec -n rag-system redis-cluster-0 -- redis-cli cluster nodes

# Fix cluster
kubectl exec -n rag-system redis-cluster-0 -- redis-cli --cluster fix <node-ip>:6379

# If necessary, rebuild cluster
kubectl delete statefulset redis-cluster -n rag-system
kubectl apply -f redis-cluster.yaml
# Reinitialize cluster
```

#### Slow Query Performance

```
Symptoms:
- Query latency spike
- Timeout errors

Diagnosis:
1. Check FAISS search latency
   # Look at metrics: faiss_search_duration_seconds

2. Check Elasticsearch performance
   curl "http://elasticsearch:9200/_nodes/stats/indices/search"

3. Check PostgreSQL slow queries
   SELECT query, mean_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;

Resolution:
# Optimize FAISS
- Reduce nprobe if too high
- Add more shards if index too large

# Optimize Elasticsearch
- Increase refresh_interval
- Add more replicas
- Optimize mapping

# Optimize PostgreSQL
- Add indexes
- Vacuum tables
- Tune query
```

### 6.2 Log Analysis

#### Finding Errors

```bash
# Recent errors in query service
kubectl logs -n rag-system deployment/query-service --tail=100 | grep ERROR

# Errors in last hour (Elasticsearch)
curl -X POST "http://elasticsearch:9200/logs-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}'

# Count errors by service
kubectl logs -n rag-system --all-containers --prefix=true | grep ERROR | cut -d' ' -f1 | sort | uniq -c
```

#### Tracing Requests

```bash
# Find trace for specific request
curl "http://jaeger:16686/api/traces?service=query-service&lookback=1h&limit=10"

# Trace slow queries
curl "http://jaeger:16686/api/traces?service=query-service&minDuration=1s"
```

---

## 7. Capacity Planning

### 7.1 Resource Monitoring

#### Current Usage

```bash
# Overall cluster usage
kubectl top nodes

# Namespace usage
kubectl top pods -n rag-system --sort-by=cpu
kubectl top pods -n rag-system --sort-by=memory

# Storage usage
kubectl get pvc -n rag-system -o custom-columns=NAME:.metadata.name,CAPACITY:.status.capacity.storage,USED:.status.used
```

#### Growth Trends

```
Query Grafana for:
- Query volume trend (last 3 months)
- Storage growth rate (GB/month)
- User growth rate
- Document upload rate

Projection Formula:
- Queries next month = Current QPS * (1 + Monthly Growth Rate)
- Storage next month = Current Storage + (Growth Rate * 30 days)
```

### 7.2 Scaling Triggers

| Metric | Current | Threshold | Action |
|--------|---------|-----------|--------|
| Query QPS | 10,000 | 8,000 | Add query pods |
| CPU Usage | 70% | 80% | Add nodes |
| Memory Usage | 75% | 85% | Add nodes |
| Storage Usage | 70% | 80% | Expand PVCs |
| Cache Hit Rate | 85% | <75% | Increase cache size |

### 7.3 Cost Optimization

```bash
# Identify expensive resources
kubectl cost -n rag-system

# Optimize pod resources
kubectl resource-capacity -n rag-system

# Right-size recommendations
kubectl vertical-pod-autoscaler -n rag-system

# Actions:
1. Scale down unused services
2. Use spot instances for workers
3. Implement pod disruption budgets
4. Use storage tiering (hot/cold)
5. Optimize cache expiration
```

---

## Appendix A: Runbook Templates

### Template: Service Restart

```
Service: <name>
Owner: <team>
Risk Level: <low/medium/high>

Pre-checks:
□ Check service health
□ Review recent changes
□ Notify #ops channel

Procedure:
1. Scale down to 0
   kubectl scale deployment <name> --replicas=0 -n rag-system

2. Wait for pods to terminate
   kubectl wait --for=delete pod -l app=<name> -n rag-system

3. Scale up
   kubectl scale deployment <name> --replicas=<N> -n rag-system

4. Verify health
   kubectl get pods -l app=<name> -n rag-system
   curl http://<service>:8000/health

Rollback:
If issues, scale back to previous replica count

Post-checks:
□ Service responding
□ No errors in logs
□ Metrics normal
```

---

**End of Operations Manual**

For architecture details, see: ARCHITECTURE.md
For deployment instructions, see: DEPLOYMENT.md
For security procedures, see: SECURITY_COMPLIANCE.md

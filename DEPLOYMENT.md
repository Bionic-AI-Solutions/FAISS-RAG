# Enterprise Multi-Modal RAG System - Deployment Guide

## Version: 1.0
## Last Updated: 2025-12-26

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Core Services Deployment](#core-services-deployment)
4. [Application Services Deployment](#application-services-deployment)
5. [Monitoring Stack](#monitoring-stack)
6. [Production Checklist](#production-checklist)

---

## 1. Prerequisites

### 1.1 Infrastructure Requirements

**Kubernetes Cluster**:
- Version: 1.27+
- Nodes: 50-100 worker nodes
- Node Types:
  - General: 16 vCPU, 64GB RAM (40 nodes)
  - High-memory: 32 vCPU, 256GB RAM (30 nodes)
  - GPU: 16 vCPU, 128GB RAM, 1-4 GPUs (10 nodes, optional)

**Storage**:
- StorageClass: `fast-ssd` (NVMe SSDs)
- Capacity: 100TB+
- IOPS: 50,000+ sustained

**Network**:
- Bandwidth: 100 Gbps inter-node
- Load Balancer: HA Proxy or cloud-native

### 1.2 Install Required Tools

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install ArgoCD CLI
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd && sudo mv argocd /usr/local/bin/

# Verify
kubectl version --client
helm version
argocd version --client
```

### 1.3 Create Namespaces

```bash
kubectl create namespace rag-system
kubectl create namespace rag-monitoring
kubectl create namespace rag-ingestion
```

---

## 2. Infrastructure Setup

### 2.1 Storage Classes

Save as `storage-classes.yaml`:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs  # Change for your environment
parameters:
  type: gp3
  iops: "16000"
  throughput: "1000"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

```bash
kubectl apply -f storage-classes.yaml
```

### 2.2 Secrets Creation

```bash
# Redis password
kubectl create secret generic redis-credentials \
  --from-literal=password=$(openssl rand -base64 32) \
  -n rag-system

# PostgreSQL credentials
kubectl create secret generic postgres-credentials \
  --from-literal=password=$(openssl rand -base64 32) \
  -n rag-system

# Elasticsearch credentials
kubectl create secret generic elasticsearch-credentials \
  --from-literal=password=$(openssl rand -base64 32) \
  -n rag-system

# Neo4j credentials
kubectl create secret generic neo4j-credentials \
  --from-literal=auth=neo4j/$(openssl rand -base64 32) \
  -n rag-system

# MinIO credentials
kubectl create secret generic minio-credentials \
  --from-literal=root-user=admin \
  --from-literal=root-password=$(openssl rand -base64 32) \
  -n rag-system

# API keys (replace with actual keys)
kubectl create secret generic llm-api-keys \
  --from-literal=anthropic-api-key=YOUR_ANTHROPIC_KEY \
  --from-literal=openai-api-key=YOUR_OPENAI_KEY \
  -n rag-system
```

---

## 3. Core Services Deployment

### 3.1 Redis Cluster

Save as `redis-cluster.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: rag-system
data:
  redis.conf: |
    bind 0.0.0.0
    port 6379
    protected-mode yes
    
    # Persistence
    save 900 1
    save 300 10
    save 60 10000
    appendonly yes
    appendfsync everysec
    
    # Memory
    maxmemory 8gb
    maxmemory-policy allkeys-lru
    
    # Performance
    slowlog-log-slower-than 10000
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: rag-system
spec:
  serviceName: redis-cluster
  replicas: 6
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - redis-cluster
            topologyKey: kubernetes.io/hostname
      containers:
      - name: redis
        image: redis:7.2-alpine
        ports:
        - containerPort: 6379
          name: client
        - containerPort: 16379
          name: gossip
        command:
        - redis-server
        - /conf/redis.conf
        - --cluster-enabled
        - "yes"
        - --cluster-config-file
        - /data/nodes.conf
        - --cluster-node-timeout
        - "5000"
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: password
        volumeMounts:
        - name: conf
          mountPath: /conf
        - name: data
          mountPath: /data
        resources:
          requests:
            cpu: 2000m
            memory: 8Gi
          limits:
            cpu: 4000m
            memory: 12Gi
      volumes:
      - name: conf
        configMap:
          name: redis-config
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis-cluster
  namespace: rag-system
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - port: 6379
    targetPort: 6379
    name: client
  - port: 16379
    targetPort: 16379
    name: gossip
  selector:
    app: redis-cluster
```

Deploy:
```bash
kubectl apply -f redis-cluster.yaml

# Wait for pods
kubectl wait --for=condition=ready pod -l app=redis-cluster -n rag-system --timeout=300s

# Initialize cluster
kubectl exec -n rag-system redis-cluster-0 -- redis-cli --cluster create \
  $(kubectl get pods -n rag-system -l app=redis-cluster -o jsonpath='{range.items[*]}{.status.podIP}:6379 {end}') \
  --cluster-replicas 1 \
  --cluster-yes
```

### 3.2 PostgreSQL

Save as `postgresql.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-init-scripts
  namespace: rag-system
data:
  01-init.sql: |
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
    
    CREATE SCHEMA IF NOT EXISTS metadata;
    CREATE SCHEMA IF NOT EXISTS audit;
    
    CREATE TABLE IF NOT EXISTS metadata.tenants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(255) NOT NULL,
        tier VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        settings JSONB
    );
    
    CREATE TABLE IF NOT EXISTS metadata.users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID REFERENCES metadata.tenants(id),
        email VARCHAR(255) NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        settings JSONB
    );
    
    CREATE TABLE IF NOT EXISTS metadata.documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID REFERENCES metadata.tenants(id),
        user_id UUID REFERENCES metadata.users(id),
        filename VARCHAR(255) NOT NULL,
        file_type VARCHAR(50),
        storage_path TEXT,
        status VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata JSONB
    );
    
    CREATE TABLE IF NOT EXISTS audit.query_logs (
        id BIGSERIAL PRIMARY KEY,
        tenant_id UUID,
        user_id UUID,
        query_text TEXT,
        results_count INTEGER,
        latency_ms INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX idx_documents_tenant ON metadata.documents(tenant_id);
    CREATE INDEX idx_query_logs_timestamp ON audit.query_logs(timestamp);
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: rag-system
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: ankane/pgvector:v0.5.1
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_USER
          value: "rag_admin"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: POSTGRES_DB
          value: "rag_system"
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        - name: init-scripts
          mountPath: /docker-entrypoint-initdb.d
        resources:
          requests:
            cpu: 4000m
            memory: 16Gi
          limits:
            cpu: 8000m
            memory: 32Gi
      volumes:
      - name: init-scripts
        configMap:
          name: postgres-init-scripts
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 500Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: rag-system
spec:
  type: ClusterIP
  ports:
  - port: 5432
    targetPort: 5432
  selector:
    app: postgres
```

Deploy:
```bash
kubectl apply -f postgresql.yaml
```

### 3.3 Elasticsearch

Save as `elasticsearch.yaml`:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: rag-system
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      initContainers:
      - name: increase-vm-max-map
        image: busybox
        command:
        - sysctl
        - -w
        - vm.max_map_count=262144
        securityContext:
          privileged: true
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
        ports:
        - containerPort: 9200
          name: http
        - containerPort: 9300
          name: transport
        env:
        - name: cluster.name
          value: rag-system-es
        - name: node.name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: discovery.seed_hosts
          value: "elasticsearch-0.elasticsearch,elasticsearch-1.elasticsearch,elasticsearch-2.elasticsearch"
        - name: cluster.initial_master_nodes
          value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
        - name: ES_JAVA_OPTS
          value: "-Xms8g -Xmx8g"
        - name: xpack.security.enabled
          value: "false"
        volumeMounts:
        - name: data
          mountPath: /usr/share/elasticsearch/data
        resources:
          requests:
            cpu: 4000m
            memory: 16Gi
          limits:
            cpu: 8000m
            memory: 32Gi
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 1Ti
---
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch
  namespace: rag-system
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - port: 9200
    targetPort: 9200
  selector:
    app: elasticsearch
```

Deploy:
```bash
kubectl apply -f elasticsearch.yaml
```

### 3.4 Neo4j

Save as `neo4j.yaml`:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: rag-system
spec:
  serviceName: neo4j
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.13
        ports:
        - containerPort: 7474
          name: http
        - containerPort: 7687
          name: bolt
        env:
        - name: NEO4J_AUTH
          valueFrom:
            secretKeyRef:
              name: neo4j-credentials
              key: auth
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            cpu: 2000m
            memory: 8Gi
          limits:
            cpu: 4000m
            memory: 16Gi
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 200Gi
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j
  namespace: rag-system
spec:
  type: ClusterIP
  ports:
  - port: 7474
    name: http
  - port: 7687
    name: bolt
  selector:
    app: neo4j
```

Deploy:
```bash
kubectl apply -f neo4j.yaml
```

### 3.5 Apache Kafka

Save as `kafka.yaml`:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
  namespace: rag-system
spec:
  serviceName: kafka
  replicas: 3
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: apache/kafka:3.6.0
        ports:
        - containerPort: 9092
          name: client
        - containerPort: 9093
          name: controller
        env:
        - name: KAFKA_HEAP_OPTS
          value: "-Xmx4G -Xms4G"
        - name: KAFKA_CFG_NODE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: KAFKA_CFG_PROCESS_ROLES
          value: "broker,controller"
        - name: KAFKA_CFG_LISTENERS
          value: "PLAINTEXT://:9092,CONTROLLER://:9093"
        - name: KAFKA_CFG_CONTROLLER_QUORUM_VOTERS
          value: "0@kafka-0.kafka:9093,1@kafka-1.kafka:9093,2@kafka-2.kafka:9093"
        volumeMounts:
        - name: data
          mountPath: /var/lib/kafka/data
        resources:
          requests:
            cpu: 2000m
            memory: 8Gi
          limits:
            cpu: 4000m
            memory: 16Gi
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 500Gi
---
apiVersion: v1
kind: Service
metadata:
  name: kafka
  namespace: rag-system
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - port: 9092
    name: client
  selector:
    app: kafka
```

Deploy:
```bash
kubectl apply -f kafka.yaml
```

### 3.6 MinIO

Save as `minio.yaml`:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: minio
  namespace: rag-system
spec:
  serviceName: minio
  replicas: 4
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
      - name: minio
        image: minio/minio:latest
        args:
        - server
        - http://minio-{0...3}.minio.rag-system.svc.cluster.local/data
        - --console-address
        - :9001
        ports:
        - containerPort: 9000
        - containerPort: 9001
        env:
        - name: MINIO_ROOT_USER
          valueFrom:
            secretKeyRef:
              name: minio-credentials
              key: root-user
        - name: MINIO_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: minio-credentials
              key: root-password
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: standard-ssd
      resources:
        requests:
          storage: 5Ti
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: rag-system
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - port: 9000
    name: api
  - port: 9001
    name: console
  selector:
    app: minio
```

Deploy:
```bash
kubectl apply -f minio.yaml
```

### 3.7 Ollama

Save as `ollama.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ollama-models-pvc
  namespace: rag-system
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 500Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: rag-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        env:
        - name: OLLAMA_NUM_PARALLEL
          value: "4"
        - name: OLLAMA_MAX_LOADED_MODELS
          value: "3"
        volumeMounts:
        - name: models
          mountPath: /root/.ollama
        resources:
          requests:
            cpu: 4000m
            memory: 16Gi
          limits:
            cpu: 8000m
            memory: 32Gi
      initContainers:
      - name: model-puller
        image: ollama/ollama:latest
        command:
        - /bin/sh
        - -c
        - |
          ollama pull llama3.1:8b
          ollama pull nomic-embed-text
        volumeMounts:
        - name: models
          mountPath: /root/.ollama
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: ollama-models-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: rag-system
spec:
  type: ClusterIP
  ports:
  - port: 11434
    targetPort: 11434
  selector:
    app: ollama
```

Deploy:
```bash
kubectl apply -f ollama.yaml
```

---

## 4. Application Services Deployment

### 4.1 Query Service

Save as `query-service.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: query-service
  namespace: rag-system
spec:
  replicas: 10
  selector:
    matchLabels:
      app: query-service
  template:
    metadata:
      labels:
        app: query-service
    spec:
      containers:
      - name: query-service
        image: your-registry/rag-query-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_HOST
          value: "redis-cluster.rag-system.svc.cluster.local"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: password
        - name: POSTGRES_HOST
          value: "postgres.rag-system.svc.cluster.local"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: ELASTICSEARCH_HOST
          value: "elasticsearch.rag-system.svc.cluster.local:9200"
        - name: NEO4J_URI
          value: "bolt://neo4j.rag-system.svc.cluster.local:7687"
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: neo4j-credentials
              key: auth
        - name: OLLAMA_HOST
          value: "http://ollama.rag-system.svc.cluster.local:11434"
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-api-keys
              key: anthropic-api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-api-keys
              key: openai-api-key
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
          limits:
            cpu: 4000m
            memory: 8Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: query-service
  namespace: rag-system
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
  selector:
    app: query-service
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: query-service-hpa
  namespace: rag-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: query-service
  minReplicas: 10
  maxReplicas: 500
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

Deploy:
```bash
kubectl apply -f query-service.yaml
```

### 4.2 Ingestion Workers

Save as `ingestion-workers.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ingestion-worker
  namespace: rag-ingestion
spec:
  replicas: 20
  selector:
    matchLabels:
      app: ingestion-worker
  template:
    metadata:
      labels:
        app: ingestion-worker
    spec:
      containers:
      - name: worker
        image: your-registry/rag-ingestion-worker:latest
        env:
        - name: KAFKA_BROKERS
          value: "kafka.rag-system.svc.cluster.local:9092"
        - name: REDIS_HOST
          value: "redis-cluster.rag-system.svc.cluster.local"
        - name: POSTGRES_HOST
          value: "postgres.rag-system.svc.cluster.local"
        - name: MINIO_ENDPOINT
          value: "minio.rag-system.svc.cluster.local:9000"
        - name: OLLAMA_HOST
          value: "http://ollama.rag-system.svc.cluster.local:11434"
        resources:
          requests:
            cpu: 4000m
            memory: 8Gi
          limits:
            cpu: 8000m
            memory: 16Gi
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ingestion-worker-hpa
  namespace: rag-ingestion
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ingestion-worker
  minReplicas: 20
  maxReplicas: 200
  metrics:
  - type: External
    external:
      metric:
        name: kafka_consumer_lag
      target:
        type: AverageValue
        averageValue: "1000"
```

Deploy:
```bash
kubectl apply -f ingestion-workers.yaml
```

### 4.3 API Gateway (Kong)

Save as `kong-gateway.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kong-proxy
  namespace: rag-system
spec:
  type: LoadBalancer
  ports:
  - name: proxy
    port: 80
    targetPort: 8000
  - name: proxy-ssl
    port: 443
    targetPort: 8443
  selector:
    app: kong
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kong
  namespace: rag-system
spec:
  replicas: 5
  selector:
    matchLabels:
      app: kong
  template:
    metadata:
      labels:
        app: kong
    spec:
      containers:
      - name: kong
        image: kong:3.4
        env:
        - name: KONG_DATABASE
          value: "off"
        - name: KONG_DECLARATIVE_CONFIG
          value: "/etc/kong/kong.yml"
        - name: KONG_PROXY_ACCESS_LOG
          value: "/dev/stdout"
        - name: KONG_ADMIN_ACCESS_LOG
          value: "/dev/stdout"
        - name: KONG_PROXY_ERROR_LOG
          value: "/dev/stderr"
        - name: KONG_ADMIN_ERROR_LOG
          value: "/dev/stderr"
        ports:
        - containerPort: 8000
          name: proxy
        - containerPort: 8443
          name: proxy-ssl
        - containerPort: 8001
          name: admin
        volumeMounts:
        - name: kong-config
          mountPath: /etc/kong
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
      volumes:
      - name: kong-config
        configMap:
          name: kong-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: kong-config
  namespace: rag-system
data:
  kong.yml: |
    _format_version: "3.0"
    
    services:
    - name: query-service
      url: http://query-service.rag-system.svc.cluster.local:8000
      routes:
      - name: query-route
        paths:
        - /api/query
      plugins:
      - name: rate-limiting
        config:
          minute: 100
          policy: local
      - name: jwt
        config:
          secret_is_base64: false
```

Deploy:
```bash
kubectl apply -f kong-gateway.yaml
```

---

## 5. Monitoring Stack

### 5.1 Prometheus

Save as `prometheus.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: rag-monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - rag-system
          - rag-ingestion
      
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: rag-monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: storage
          mountPath: /prometheus
        resources:
          requests:
            cpu: 2000m
            memory: 8Gi
          limits:
            cpu: 4000m
            memory: 16Gi
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: rag-monitoring
spec:
  type: ClusterIP
  ports:
  - port: 9090
  selector:
    app: prometheus
```

Deploy:
```bash
kubectl apply -f prometheus.yaml
```

### 5.2 Grafana

Save as `grafana.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: rag-monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin"  # Change this!
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: rag-monitoring
spec:
  type: LoadBalancer
  ports:
  - port: 3000
  selector:
    app: grafana
```

Deploy:
```bash
kubectl apply -f grafana.yaml
```

---

## 6. Production Checklist

### 6.1 Pre-Deployment

- [ ] All secrets created
- [ ] Storage classes configured
- [ ] Network policies applied
- [ ] Resource quotas set
- [ ] TLS certificates generated
- [ ] DNS records configured
- [ ] Backup strategy implemented

### 6.2 Post-Deployment Verification

```bash
# Check all pods are running
kubectl get pods -n rag-system
kubectl get pods -n rag-ingestion
kubectl get pods -n rag-monitoring

# Check services
kubectl get svc -n rag-system

# Check PVCs
kubectl get pvc -n rag-system

# Test Redis cluster
kubectl exec -n rag-system redis-cluster-0 -- redis-cli cluster info

# Test Elasticsearch
kubectl exec -n rag-system elasticsearch-0 -- curl -X GET "localhost:9200/_cluster/health?pretty"

# Test Kafka
kubectl exec -n rag-system kafka-0 -- /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Check query service
kubectl port-forward -n rag-system svc/query-service 8000:8000
curl http://localhost:8000/health
```

### 6.3 Create Kafka Topics

```bash
kubectl exec -n rag-system kafka-0 -- /opt/kafka/bin/kafka-topics.sh \
  --create --topic ingestion_requests \
  --bootstrap-server localhost:9092 \
  --partitions 30 \
  --replication-factor 3

kubectl exec -n rag-system kafka-0 -- /opt/kafka/bin/kafka-topics.sh \
  --create --topic query_events \
  --bootstrap-server localhost:9092 \
  --partitions 30 \
  --replication-factor 3
```

### 6.4 Initialize MinIO Buckets

```bash
kubectl run -n rag-system minio-client --rm -it --image=minio/mc --restart=Never -- bash

# Inside the pod:
mc alias set myminio http://minio:9000 admin <password>
mc mb myminio/documents
mc mb myminio/backups
exit
```

---

## 7. Troubleshooting

### Common Issues

**Pods not starting:**
```bash
kubectl describe pod <pod-name> -n rag-system
kubectl logs <pod-name> -n rag-system
```

**Storage issues:**
```bash
kubectl get pvc -n rag-system
kubectl describe pvc <pvc-name> -n rag-system
```

**Network connectivity:**
```bash
kubectl run -n rag-system debug --rm -it --image=nicolaka/netshoot -- bash
# Test connectivity to services
```

**Redis cluster not forming:**
```bash
# Check cluster status
kubectl exec -n rag-system redis-cluster-0 -- redis-cli cluster nodes

# Manually fix cluster
kubectl exec -n rag-system redis-cluster-0 -- redis-cli --cluster fix <node-ip>:6379
```

---

## Next Steps

1. Deploy application code (Query Service, Ingestion Workers)
2. Configure monitoring dashboards in Grafana
3. Set up alerting rules in Prometheus
4. Configure backup jobs
5. Perform load testing
6. Review security settings
7. Document operational procedures

For API specifications, see: API_SPECIFICATION.md
For implementation roadmap, see: IMPLEMENTATION_ROADMAP.md

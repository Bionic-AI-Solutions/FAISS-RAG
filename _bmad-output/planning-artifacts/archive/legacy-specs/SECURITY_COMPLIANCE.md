# Enterprise Multi-Modal RAG System - Security & Compliance Guide

## Version: 1.0
## Last Updated: 2025-12-26

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Encryption](#encryption)
4. [Network Security](#network-security)
5. [Compliance](#compliance)
6. [Security Monitoring](#security-monitoring)
7. [Incident Response](#incident-response)

---

## 1. Security Overview

### 1.1 Security Principles

**Defense in Depth:**
- Multiple layers of security controls
- Network segmentation
- Least privilege access
- Zero trust architecture

**Security by Default:**
- Encryption enabled by default
- Secure defaults for all services
- Mandatory authentication
- Automatic security updates

### 1.2 Threat Model

| Threat | Risk Level | Mitigation |
|--------|-----------|------------|
| Unauthorized access | High | Multi-factor auth, RBAC |
| Data breach | Critical | Encryption, tenant isolation |
| DDoS attack | High | Rate limiting, CDN |
| Insider threat | Medium | Audit logging, access controls |
| Supply chain attack | Medium | Dependency scanning, signatures |
| Data exfiltration | High | DLP, egress filtering |

---

## 2. Authentication & Authorization

### 2.1 Authentication Methods

#### JWT-Based Authentication

```python
# Token Generation
from jose import jwt
from datetime import datetime, timedelta

def generate_token(user_id: str, tenant_id: str) -> str:
    """Generate JWT access token"""
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "iss": "rag-system"
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

# Token Validation
def validate_token(token: str) -> dict:
    """Validate and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

#### Multi-Factor Authentication (MFA)

```python
# MFA Configuration
import pyotp

def setup_mfa(user_id: str) -> dict:
    """Setup TOTP-based MFA"""
    secret = pyotp.random_base32()
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_id,
        issuer_name="RAG System"
    )
    
    # Store secret in Vault
    vault.write(f"mfa/{user_id}", secret=secret)
    
    return {
        "secret": secret,
        "qr_code_uri": totp_uri
    }

def verify_mfa(user_id: str, token: str) -> bool:
    """Verify MFA token"""
    secret = vault.read(f"mfa/{user_id}")["secret"]
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)
```

### 2.2 Role-Based Access Control (RBAC)

#### Role Definitions

```yaml
roles:
  admin:
    permissions:
      - documents:*
      - users:*
      - tenants:*
      - analytics:*
      - settings:*
  
  user:
    permissions:
      - documents:read
      - documents:write
      - documents:delete (own only)
      - query:execute
      - sessions:manage
  
  viewer:
    permissions:
      - documents:read
      - query:execute
  
  analyst:
    permissions:
      - documents:read
      - query:execute
      - analytics:read
```

#### Permission Enforcement

```python
# Permission Decorator
from functools import wraps

def require_permission(permission: str):
    """Decorator to enforce permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from token
            user = get_current_user()
            
            # Check permission
            if not has_permission(user, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@app.delete("/documents/{document_id}")
@require_permission("documents:delete")
async def delete_document(document_id: str):
    # Implementation
    pass
```

### 2.3 Tenant Isolation

```python
# Tenant Context Middleware
class TenantMiddleware:
    async def __call__(self, request: Request, call_next):
        # Extract tenant ID from header
        tenant_id = request.headers.get("X-Tenant-ID")
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant ID required")
        
        # Validate tenant access
        user = get_current_user(request)
        if user.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant access denied")
        
        # Set tenant context
        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        return response

# Database Query with Tenant Filtering
async def get_documents(tenant_id: str, user_id: str):
    """Get documents with automatic tenant filtering"""
    query = """
    SELECT * FROM metadata.documents
    WHERE tenant_id = $1 AND user_id = $2
    """
    return await db.fetch(query, tenant_id, user_id)
```

---

## 3. Encryption

### 3.1 Encryption at Rest

#### Database Encryption

```yaml
# PostgreSQL Encryption
postgresql:
  encryption:
    method: AES-256
    key_rotation: quarterly
    tde_enabled: true  # Transparent Data Encryption
    
  configuration:
    ssl_mode: require
    ssl_cert_file: /certs/server.crt
    ssl_key_file: /certs/server.key
    ssl_ca_file: /certs/ca.crt
```

#### Storage Encryption

```yaml
# Kubernetes StorageClass with encryption
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-west-2:123456789:key/abc-123"
```

#### Application-Level Encryption

```python
# Document Encryption Service
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

class EncryptionService:
    def __init__(self, vault_client):
        self.vault = vault_client
    
    def encrypt_document(
        self,
        data: bytes,
        tenant_id: str,
        document_id: str
    ) -> dict:
        """Encrypt document with tenant-specific DEK"""
        
        # Get Data Encryption Key from Vault
        dek_path = f"tenants/{tenant_id}/dek"
        dek_response = self.vault.secrets.kv.v2.read_secret(path=dek_path)
        dek = bytes.fromhex(dek_response['data']['key'])
        
        # Generate nonce
        nonce = os.urandom(12)
        
        # Encrypt
        cipher = Cipher(
            algorithms.AES(dek),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return {
            'ciphertext': ciphertext,
            'nonce': nonce,
            'tag': encryptor.tag,
            'algorithm': 'AES-256-GCM',
            'key_version': dek_response['metadata']['version']
        }
    
    def decrypt_document(
        self,
        ciphertext: bytes,
        nonce: bytes,
        tag: bytes,
        tenant_id: str
    ) -> bytes:
        """Decrypt document"""
        
        # Get DEK from Vault
        dek_path = f"tenants/{tenant_id}/dek"
        dek_response = self.vault.secrets.kv.v2.read_secret(path=dek_path)
        dek = bytes.fromhex(dek_response['data']['key'])
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(dek),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext
```

### 3.2 Encryption in Transit

#### TLS Configuration

```yaml
# Ingress TLS
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rag-ingress
  namespace: rag-system
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.3"
    nginx.ingress.kubernetes.io/ssl-ciphers: "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256"
spec:
  tls:
  - hosts:
    - api.rag-system.com
    secretName: rag-tls-cert
  rules:
  - host: api.rag-system.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: query-service
            port:
              number: 8000
```

#### mTLS Between Services

```yaml
# Service Mesh mTLS (Istio)
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: rag-system
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: query-service-authz
  namespace: rag-system
spec:
  selector:
    matchLabels:
      app: query-service
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/rag-system/sa/api-gateway"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/v1/query"]
```

### 3.3 Key Management

#### Vault Configuration

```bash
# Initialize Vault
vault operator init -key-shares=5 -key-threshold=3

# Enable KV secrets engine
vault secrets enable -path=secret kv-v2

# Enable transit engine for encryption as a service
vault secrets enable transit

# Create encryption key
vault write -f transit/keys/rag-system

# Enable auto-unseal with AWS KMS
vault operator init \
  -key-shares=1 \
  -key-threshold=1 \
  -recovery-shares=5 \
  -recovery-threshold=3
```

#### Key Rotation

```python
# Automated Key Rotation
import schedule
import time

def rotate_dek(tenant_id: str):
    """Rotate tenant Data Encryption Key"""
    
    # Generate new key
    new_dek = os.urandom(32)
    
    # Store in Vault with new version
    vault.secrets.kv.v2.create_or_update_secret(
        path=f"tenants/{tenant_id}/dek",
        secret={'key': new_dek.hex()}
    )
    
    # Schedule re-encryption of documents (async job)
    schedule_reencryption(tenant_id)
    
    # Log rotation
    audit_log.info(f"Rotated DEK for tenant {tenant_id}")

# Schedule quarterly rotation
schedule.every(90).days.do(rotate_all_tenant_keys)

while True:
    schedule.run_pending()
    time.sleep(3600)
```

---

## 4. Network Security

### 4.1 Network Policies

```yaml
# Deny all ingress by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: rag-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
# Allow specific service communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: query-service-policy
  namespace: rag-system
spec:
  podSelector:
    matchLabels:
      app: query-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: elasticsearch
    ports:
    - protocol: TCP
      port: 9200
```

### 4.2 Firewall Rules

```bash
# Allow only required ports
iptables -A INPUT -p tcp --dport 443 -j ACCEPT  # HTTPS
iptables -A INPUT -p tcp --dport 6443 -j ACCEPT # Kubernetes API
iptables -A INPUT -p tcp --dport 22 -j ACCEPT   # SSH (jump box only)
iptables -A INPUT -j DROP  # Drop all other traffic

# Egress filtering
iptables -A OUTPUT -d 169.254.169.254 -j DROP  # Block metadata service
iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT  # Allow SSH out
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT # Allow HTTPS out
iptables -A OUTPUT -j DROP  # Drop all other outbound
```

### 4.3 DDoS Protection

```yaml
# Rate Limiting Configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: kong-rate-limiting
  namespace: rag-system
data:
  config.yml: |
    plugins:
    - name: rate-limiting
      config:
        second: 100
        minute: 1000
        hour: 10000
        policy: redis
        redis_host: redis-cluster
        redis_port: 6379
        fault_tolerant: true
    
    - name: request-size-limiting
      config:
        allowed_payload_size: 10  # 10MB
    
    - name: ip-restriction
      config:
        whitelist: []
        blacklist: []  # Populated by threat intelligence
```

---

## 5. Compliance

### 5.1 HIPAA Compliance

#### Technical Safeguards

```yaml
hipaa_requirements:
  access_controls:
    - unique_user_ids: ✓
    - emergency_access: ✓
    - automatic_logoff: ✓
    - encryption_decryption: ✓
  
  audit_controls:
    - activity_logging: ✓
    - log_retention: 7_years
    - log_integrity: ✓
  
  integrity_controls:
    - data_authentication: ✓
    - checksums: ✓
  
  transmission_security:
    - encryption: TLS 1.3
    - integrity_controls: ✓
```

#### Implementation

```python
# HIPAA Audit Logging
class HIPAAAuditLogger:
    async def log_phi_access(
        self,
        user_id: str,
        action: str,
        resource_id: str,
        result: str
    ):
        """Log PHI access for HIPAA compliance"""
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": "phi",
            "resource_id": resource_id,
            "result": result,
            "ip_address": get_client_ip(),
            "user_agent": get_user_agent()
        }
        
        # Store in tamper-evident log
        await timescaledb.insert("audit.phi_access", audit_entry)
        
        # Also send to SIEM
        await siem.send(audit_entry)

# BAA (Business Associate Agreement) Verification
@app.post("/documents/upload")
@require_baa_acceptance
async def upload_document(document: UploadFile):
    """Upload with BAA verification"""
    # Implementation
    pass
```

### 5.2 GDPR Compliance

#### Data Subject Rights

```python
# Right to Access
async def export_user_data(user_id: str, tenant_id: str) -> dict:
    """Export all user data (GDPR Article 15)"""
    
    data = {
        "personal_info": await db.fetch_user(user_id),
        "documents": await db.fetch_user_documents(user_id),
        "queries": await db.fetch_user_queries(user_id),
        "sessions": await db.fetch_user_sessions(user_id)
    }
    
    # Log export request
    await audit_log("gdpr_export", user_id=user_id)
    
    return data

# Right to Erasure
async def delete_user_data(user_id: str, tenant_id: str):
    """Delete all user data (GDPR Article 17)"""
    
    # Delete from all systems
    await db.delete_user(user_id)
    await faiss_manager.delete_user_vectors(user_id)
    await elasticsearch.delete_user_documents(user_id)
    await neo4j.delete_user_nodes(user_id)
    await redis.delete_user_sessions(user_id)
    await minio.delete_user_files(user_id)
    
    # Log deletion
    await audit_log("gdpr_deletion", user_id=user_id)
    
    # Verify deletion
    assert await verify_user_deletion(user_id)

# Right to Portability
async def export_portable_data(user_id: str) -> bytes:
    """Export data in portable format (GDPR Article 20)"""
    
    data = await export_user_data(user_id)
    
    # Convert to JSON
    json_data = json.dumps(data, indent=2)
    
    return json_data.encode('utf-8')
```

#### Consent Management

```python
class ConsentManager:
    async def record_consent(
        self,
        user_id: str,
        purpose: str,
        consent_given: bool
    ):
        """Record user consent"""
        
        consent_record = {
            "user_id": user_id,
            "purpose": purpose,
            "consent_given": consent_given,
            "timestamp": datetime.utcnow(),
            "ip_address": get_client_ip()
        }
        
        await db.insert("consent_records", consent_record)
    
    async def check_consent(self, user_id: str, purpose: str) -> bool:
        """Check if user has consented to purpose"""
        
        consent = await db.fetch_one(
            "SELECT consent_given FROM consent_records "
            "WHERE user_id = $1 AND purpose = $2 "
            "ORDER BY timestamp DESC LIMIT 1",
            user_id, purpose
        )
        
        return consent['consent_given'] if consent else False
```

### 5.3 SOC 2 Compliance

#### Control Implementation

```yaml
soc2_controls:
  cc6_1_logical_access:
    - multi_factor_authentication: ✓
    - role_based_access: ✓
    - session_timeout: ✓
    - password_complexity: ✓
  
  cc6_6_encryption:
    - data_at_rest: AES-256
    - data_in_transit: TLS 1.3
    - key_management: Vault
  
  cc7_2_monitoring:
    - security_monitoring: ✓
    - intrusion_detection: ✓
    - log_aggregation: ✓
    - alerting: ✓
  
  cc8_1_change_management:
    - change_approval: ✓
    - version_control: ✓
    - testing_procedures: ✓
```

---

## 6. Security Monitoring

### 6.1 Security Information and Event Management (SIEM)

```python
# Security Event Detection
class SecurityMonitor:
    def __init__(self):
        self.rules = [
            BruteForceDetector(),
            AnomalousAccessDetector(),
            DataExfiltrationDetector(),
            PrivilegeEscalationDetector()
        ]
    
    async def analyze_event(self, event: dict):
        """Analyze security event"""
        
        for rule in self.rules:
            if await rule.matches(event):
                alert = await rule.create_alert(event)
                await self.send_alert(alert)
    
    async def send_alert(self, alert: dict):
        """Send security alert"""
        
        # Log to SIEM
        await siem.log(alert)
        
        # Page security team if critical
        if alert['severity'] == 'critical':
            await pagerduty.trigger(alert)
        
        # Post to Slack
        await slack.post('#security-alerts', alert)

# Brute Force Detection
class BruteForceDetector:
    async def matches(self, event: dict) -> bool:
        """Detect brute force attempts"""
        
        if event['type'] != 'auth_failure':
            return False
        
        # Count failures in last 5 minutes
        failures = await redis.incr(
            f"auth_failures:{event['user_id']}",
            expire=300
        )
        
        return failures > 5
    
    async def create_alert(self, event: dict) -> dict:
        """Create brute force alert"""
        
        return {
            'type': 'brute_force_attempt',
            'severity': 'high',
            'user_id': event['user_id'],
            'ip_address': event['ip_address'],
            'timestamp': datetime.utcnow(),
            'action': 'account_locked'
        }
```

### 6.2 Vulnerability Scanning

```bash
# Container Image Scanning
trivy image your-registry/rag-query-service:latest

# Kubernetes Security Scanning
kube-bench run --targets master,node,policies

# Dependency Scanning
safety check --json
npm audit --json

# Regular Scan Schedule
# Daily: Container images
# Weekly: Kubernetes cluster
# Monthly: Full infrastructure scan
```

### 6.3 Penetration Testing

```yaml
penetration_testing:
  frequency: quarterly
  scope:
    - api_endpoints
    - authentication_mechanisms
    - authorization_controls
    - encryption_implementation
    - network_segmentation
    - tenant_isolation
  
  methodology:
    - reconnaissance
    - vulnerability_scanning
    - exploitation
    - post_exploitation
    - reporting
  
  remediation:
    critical: 24_hours
    high: 7_days
    medium: 30_days
    low: 90_days
```

---

## 7. Incident Response

### 7.1 Security Incident Response Plan

```
Phase 1: Detection & Analysis
├─ Identify security event
├─ Assess severity
├─ Classify incident type
└─ Activate response team

Phase 2: Containment
├─ Short-term containment (isolate affected systems)
├─ Evidence preservation
├─ Long-term containment (patch, reconfigure)
└─ Document actions

Phase 3: Eradication
├─ Remove malware/unauthorized access
├─ Close vulnerabilities
├─ Strengthen security controls
└─ Verify eradication

Phase 4: Recovery
├─ Restore systems
├─ Verify functionality
├─ Monitor for recurrence
└─ Return to normal operations

Phase 5: Post-Incident
├─ Root cause analysis
├─ Lessons learned
├─ Update procedures
└─ Implement improvements
```

### 7.2 Data Breach Response

```python
# Data Breach Handler
class DataBreachHandler:
    async def handle_breach(self, incident: dict):
        """Handle data breach incident"""
        
        # 1. Contain breach
        await self.contain_breach(incident)
        
        # 2. Assess impact
        affected_users = await self.assess_impact(incident)
        
        # 3. Notify stakeholders
        if len(affected_users) > 500:
            # Notify authorities (GDPR: within 72 hours)
            await self.notify_dpa(incident)
        
        # Notify affected users
        await self.notify_users(affected_users, incident)
        
        # 4. Document breach
        await self.document_breach(incident)
        
        # 5. Remediate
        await self.remediate(incident)
    
    async def notify_users(self, users: List[str], incident: dict):
        """Notify affected users"""
        
        for user in users:
            notification = {
                'subject': 'Security Incident Notification',
                'body': self.create_notification(incident),
                'user_id': user
            }
            
            await email_service.send(notification)
```

---

## Appendix A: Security Checklist

### Pre-Production Security Review

- [ ] All services require authentication
- [ ] RBAC policies configured
- [ ] Encryption at rest enabled
- [ ] TLS 1.3 for all communications
- [ ] Network policies in place
- [ ] Secrets in Vault (not hardcoded)
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] Input validation implemented
- [ ] SQL injection prevented
- [ ] XSS protection enabled
- [ ] CSRF protection enabled
- [ ] Security headers configured
- [ ] Vulnerability scan passed
- [ ] Penetration test completed
- [ ] Compliance requirements met

---

**End of Security & Compliance Guide**

For architecture details, see: ARCHITECTURE.md
For operations procedures, see: OPERATIONS.md
For configuration reference, see: CONFIGURATION_REFERENCE.md

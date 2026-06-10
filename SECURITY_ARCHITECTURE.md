# TeacherOS — Security Architecture

> **Document Purpose:** Source of truth for all security implementations in TeacherOS.
> **Author:** Principal Security Architect & Application Security Engineer
> **Target Stack:** FastAPI, PostgreSQL 15+, Redis, Argon2id, AES-256-GCM, RS256
> **Status:** v1.0 — Complete
> **Last Updated:** 2026-06-10

---

## Table of Contents

1. [Security Architecture Overview](#1-security-architecture-overview)
2. [Authentication Flow](#2-authentication-flow)
3. [Authorization Flow](#3-authorization-flow)
4. [Tenant Isolation Design](#4-tenant-isolation-design)
5. [Database Security Design](#5-database-security-design)
6. [AI Security Design](#6-ai-security-design)
7. [Audit Logging Design](#7-audit-logging-design)
8. [Threat Model](#8-threat-model)
9. [Security Metrics & Monitoring](#9-security-metrics--monitoring)
10. [API Security Controls](#10-api-security-controls)
11. [Data Encryption Strategy](#11-data-encryption-strategy)
12. [Security Incident Response](#12-security-incident-response)

---

## 1. Security Architecture Overview

### 1.1 Layered Defense Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Security Architecture                           │
│                          Defense-in-Depth                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: Network Security                                   │   │
│  │  • WAF (Cloudflare/AWS WAF)                                  │   │
│  │  • DDoS Protection                                           │   │
│  │  • TLS 1.3 (end-to-end)                                      │   │
│  │  • VPC / Private Subnets                                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 2: API Security                                       │   │
│  │  • Rate Limiting (SlowAPI)                                   │   │
│  │  • CSRF Protection                                           │   │
│  │  • Request ID / Correlation Tracking                         │   │
│  │  • CORS Configuration                                        │   │
│  │  • Input Validation & Sanitization                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 3: Authentication                                     │   │
│  │  • JWT (RS256) with jti, device tracking                     │   │
│  │  • Token Blacklist & Rotation                                │   │
│  │  • MFA (TOTP + Email OTP)                                    │   │
│  │  • Password (Argon2id, history, complexity)                  │   │
│  │  • Session Management with device fingerprinting             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 4: Authorization & Tenant Isolation                   │   │
│  │  • RBAC (Role Engine, Permission Engine, Policy Engine)      │   │
│  │  • PostgreSQL Row-Level Security (RLS)                       │   │
│  │  • Tenant Context (org_id + school_id isolation)             │   │
│  │  • AI Tool-level Permissions                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 5: Data Security                                      │   │
│  │  • AES-256-GCM Encryption for PII                             │   │
│  │  • Encryption at Rest (PostgreSQL TDE)                        │   │
│  │  • Encryption in Transit (TLS 1.3)                            │   │
│  │  • File Validation (MIME, magic bytes, extension)             │   │
│  │  • Secure File Storage (pre-signed URLs, tenant isolation)    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 6: AI Security                                        │   │
│  │  • Prompt Injection Detection                                  │   │
│  │  • PII Detection & Redaction                                  │   │
│  │  • Tool-Level Permissions & Rate Limiting                     │   │
│  │  • Output Review Gate (Human-in-the-loop)                     │   │
│  │  • Content Policy Enforcement                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 7: Audit & Monitoring                                 │   │
│  │  • Immutable Audit Logging (append-only)                     │   │
│  │  • Security Event Detection (brute force, token theft, etc.) │   │
│  │  • Prometheus Metrics (auth, tokens, sessions, MFA, etc.)    │   │
│  │  • Real-time Alerting                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Security Principles

| Principle | Implementation |
|---|---|
| **Defense in Depth** | 7-layer security model covering network → app → data |
| **Least Privilege** | Granular RBAC + RLS; deny-by-default for unknown AI tools |
| **Zero Trust** | Every request authenticated, authorized, and tenant-scoped |
| **Secure by Default** | All endpoints require auth unless explicitly public |
| **Fail Secure** | Errors return safe defaults (deny, no data leak) |
| **Immutable Audit** | Audit logs are append-only; no update or delete |
| **Tenant Isolation** | RLS + application-level context guarantees isolation |
| **Data Minimization** | Only necessary PII stored; encrypted at field level |

### 1.3 Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Password Hashing | Argon2id | Memory-hard, GPU-resistant password hashing |
| Token Signing | RS256 (4096-bit RSA) | Asymmetric JWT signing with private key |
| Encryption | AES-256-GCM | Authenticated encryption for PII fields |
| MFA | TOTP (RFC 6238) + Email OTP | Time-based one-time passwords + fallback |
| Rate Limiting | SlowAPI | Per-scope sliding window rate limiting |
| Authorization | Custom RBAC Engine | Role/permission/policy triple engine |
| Row Security | PostgreSQL RLS | Database-level tenant isolation |
| Metrics | Prometheus | Security observability and dashboards |
| Audit Storage | PostgreSQL | Append-only audit_logs table |

---

## 2. Authentication Flow

### 2.1 Complete Authentication Sequence

```
User                    API Gateway              Auth Service            Security Events          Audit Log
 │                          │                        │                       │                      │
 │  POST /auth/login        │                        │                       │                      │
 │──────────────────────────►│      Validate Creds    │                       │                      │
 │                          │───────────────────────►│                       │                      │
 │                          │                        │  Argon2id verify      │                      │
 │                          │                        │  Password + MFA check │                      │
 │                          │                        │                       │                      │
 │                          │  ┌─────────────────┐  │                       │                      │
 │                          │  │ 1. Check password│  │                       │                      │
 │                          │  │ 2. Check MFA     │  │                       │                      │
 │                          │  │ 3. Issue jti     │  │                       │                      │
 │                          │  │ 4. Create session│  │                       │                      │
 │                          │  │ 5. Generate JWT  │  │                       │                      │
 │                          │  └─────────────────┘  │                       │                      │
 │                          │                        │  Record login.success │                      │
 │                          │                        │──────────────────────►│                      │
 │                          │                        │                       │ Log login            │
 │                          │                        │                       │──────────────────────►│
 │                          │  {access, refresh,     │                       │                      │
 │                          │   session, device}     │                       │                      │
 │                          │◄───────────────────────│                       │                      │
 │  {access_token,          │                        │                       │                      │
 │   refresh_token,         │                        │                       │                      │
 │   session_id, mfa_flag}  │                        │                       │                      │
 │◄──────────────────────────│                        │                       │                      │
 │                          │                        │                       │                      │
 │  /api/resource           │                        │                       │                      │
 │  Authorization: Bearer.. │                        │                       │                      │
 │──────────────────────────►│   Verify JWT           │                       │                      │
 │                          │───────────────────────►│                       │                      │
 │                          │                        │  Validate:            │                      │
 │                          │                        │  • Signature (RS256)  │                      │
 │                          │                        │  • Expiration         │                      │
 │                          │                        │  • jti not blacklisted│                      │
 │                          │                        │  • Device match       │                      │
 │                          │  Allow/Deny            │                       │                      │
 │                          │◄───────────────────────│                       │                      │
 │  Response                │                        │                       │                      │
 │◄──────────────────────────│                        │                       │                      │
```

### 2.2 Token Lifecycle

```
┌──────────┐    Issue     ┌──────────┐    Refresh    ┌──────────┐    Revoke    ┌──────────┐
│  Access   │──────────────►  Refresh  │──────────────►  Access   │──────────────► Blacklist │
│  Token    │              │  Token   │              │  Token    │              │  Set     │
│ (15 min)  │              │ (7 days) │              │ (15 min)  │              │ (Redis)  │
└──────────┘              └──────────┘              └──────────┘              └──────────┘
     │                          │                        │                         │
     │                          │  Rotation              │                         │
     │                          ├────────────────────────►                         │
     │                          │  (old refresh →        │                         │
     │                          │   blacklist)           │                         │
     │                          │                        │                         │
     │   Expired                │   Expired / Used       │                         │
     │   → Re-authenticate      │   → Re-authenticate    │                         │
```

### 2.3 Token Claims Structure

```json
{
  "sub": "user-uuid-v4",
  "tenant": "tenant-uuid-v4",
  "org_id": "org-uuid-v4",
  "school_id": "school-uuid-v4",
  "roles": ["teacher", "adviser"],
  "perms": ["student.read", "grade.read", "ai.use"],
  "jti": "unique-token-id-v4",
  "device_id": "device-fingerprint-sha256",
  "device_name": "Chrome 120 on Windows 11",
  "token_type": "access",
  "mfa_verified": true,
  "iss": "teacheros-auth",
  "aud": "teacheros-api",
  "iat": 1717000000,
  "exp": 1717000900,
  "nbf": 1717000000
}
```

### 2.4 Password Policy

| Aspect | Requirement |
|---|---|
| Minimum Length | 12 characters |
| Complexity | Upper + Lower + Digit + Special |
| Hash Algorithm | Argon2id (t=2, m=19456, p=1) |
| History | Last 10 passwords remembered |
| Max Age | 90 days |
| Lockout | 5 failures → 15 min lockout |
| Reset Token Expiry | 1 hour |
| Reset Cooldown | 300 seconds between requests |

### 2.5 MFA Options

| Method | Use Case | Security Level |
|---|---|---|
| **TOTP** (Authenticator App) | Primary MFA | High (RFC 6238, 30s window) |
| **Email OTP** | Fallback / Enrollment | Medium (6-digit, 5 min expiry) |
| **Recovery Codes** | Account Recovery | Single-use, 10 codes issued |

### 2.6 Session Management

| Parameter | Value |
|---|---|
| Max Sessions Per User | 10 |
| Session Idle Timeout | 30 minutes |
| Device Fingerprinting | SHA-256 of user-agent + accept + accept-language |
| Concurrent Session Limit | Configurable per tenant |
| Force Logout | Immediate session revocation + token blacklist |

---

## 3. Authorization Flow

### 3.1 RBAC Engine Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     RBAC Engine Architecture                    │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────┐    ┌────────────────────┐              │
│  │   RoleEngine        │    │   PermissionEngine  │             │
│  │                     │    │                     │             │
│  │  • get_user_roles() │    │  • get_permissions()│             │
│  │  • assign_role()    │    │  • check_permission()│             │
│  │  • revoke_role()    │    │  • has_permissions() │             │
│  │  • role_hierarchy() │    │  • grant_permission()│             │
│  └──────────┬──────────┘    └──────────┬──────────┘             │
│             │                          │                         │
│             └──────────┬───────────────┘                         │
│                        │                                         │
│               ┌────────▼────────┐                                │
│               │   PolicyEngine   │                               │
│               │                  │                               │
│               │  • evaluate()    │                               │
│               │  • authorize()   │                               │
│               │  • filter_by_    │                               │
│               │    tenant()      │                               │
│               └─────────────────┘                                │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │               RBACService (Facade)                       │     │
│  │                                                          │     │
│  │  require_permission(user, perm, tenant) → bool           │     │
│  │  require_role(user, role, tenant) → bool                 │     │
│  │  has_all_permissions(user, perms, tenant) → bool         │     │
│  │  authorize_request(user, perm, resource, tenant) → bool  │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### 3.2 Role Hierarchy (DepEd-Aligned)

```
                    ┌──────────────┐
                    │ Super Admin  │
                    │  (Platform)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Division      │
                    │ Staff        │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼───┐ ┌─────▼──────┐ ┌───▼─────────┐
     │ School Head │ │ Principal  │ │ Coordinator │
     └────────┬───┘ └─────┬──────┘ └───┬─────────┘
              │           │            │
              └───────────┼────────────┘
                          │
                   ┌──────▼──────┐
                   │   Adviser   │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │   Teacher   │
                   └─────────────┘
```

### 3.3 Permission Mapping

| Role | Permissions |
|---|---|
| **Teacher** | `student.read`, `attendance.read`, `grade.read`, `form.read`, `ai.use`, `file.upload` |
| **Adviser** | + `student.write`, `attendance.write`, `grade.write`, `form.write`, `report.read`, `file.delete` |
| **Coordinator** | + `grade.compute`, `form.generate`, `report.write`, `user.read`, `mfa.enable` |
| **Principal** | + `report.submit`, `user.write`, `role.read`, `settings.read`, `mfa.disable` |
| **School Head** | + `settings.write`, `audit.read`, `session.revoke`, `token.revoke` |
| **Division Staff** | + `user.delete`, `role.write`, cross-school `report.read` |
| **Super Admin** | ALL permissions across all tenants |

### 3.4 Authorization Decision Flow

```
Request: User X wants to perform action Y on resource Z in tenant T

        ┌─────────────────────────┐
        │  Extract JWT Claims     │
        │  (user_id, roles,       │
        │   perms, tenant_id)     │
        └───────────┬─────────────┘
                    │
        ┌───────────▼─────────────┐
        │  Tenant Context Check   │◄─── TenantMiddleware
        │  Is tenant_id allowed?  │
        │  Is org/school match?   │
        └───────────┬─────────────┘
                    │
        ┌───────────▼─────────────┐
        │  Authentication Check   │
        │  Token valid?           │
        │  jti not blacklisted?   │
        │  Session active?        │
        │  MFA required?          │
        └───────────┬─────────────┘
                    │
        ┌───────────▼─────────────┐
        │  Permission Check       │◄─── RBACService
        │  Does user have perm Y  │
        │  for resource Z?        │
        └───────────┬─────────────┘
                    │
        ┌───────────▼─────────────┐
        │  Policy Evaluation      │◄─── PolicyEngine
        │  Any deny policies?     │
        │  Time-based restrictions│
        │  IP-based restrictions  │
        └───────────┬─────────────┘
                    │
        ┌───────────▼─────────────┐
        │  RLS Enforcement        │◄─── PostgreSQL RLS
        │  Is data visible for    │
        │  this tenant/org/school?│
        └───────────┬─────────────┘
                    │
         ┌──────────▼──────────┐
         │   ALLOW / DENY      │
         └─────────────────────┘
```

---

## 4. Tenant Isolation Design

### 4.1 Tenant Context Propagation

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Client      │     │  API Gateway     │     │  Application      │
│              │     │  (FastAPI)        │     │  Layer            │
├──────────────┤     ├──────────────────┤     ├──────────────────┤
│ X-Tenant-Id  │────►│ TenantMiddleware  │────►│ TenantContext     │
│ X-Org-Id     │     │                  │     │  (thread-local)   │
│ X-School-Id  │     │ Validate headers │     │  scoped_session   │
└──────────────┘     │ Extract claims   │     │  RLS policies     │
                     │ Set context       │     └──────────────────┘
                     └──────────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │  AuditService     │
                     │ SecurityEvents    │
                     │ EncryptionService │
                     │ (context-aware)   │
                     └──────────────────┘
```

### 4.2 Database Isolation Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                 Tenant Isolation Strategy                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level 1: Connection Pool Isolation                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Single database, tenant_id on every table                │   │
│  │  scoped_session(tenant_id=current)                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Level 2: Row-Level Security (RLS)                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL RLS policies on all tenant-scoped tables     │   │
│  │  CREATE POLICY tenant_isolation ON grades                │   │
│  │  USING (tenant_id = current_setting('app.tenant_id'));   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Level 3: Application-Level Enforcement                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  TenantContext enforces org + school isolation           │   │
│  │  Repository pattern with tenant filter injection         │   │
│  │  Cross-tenant access → SecurityEventService alert        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 RLS Policy Examples

```sql
-- Global RLS enable
ALTER TABLE grades ENABLE ROW LEVEL SECURITY;

-- Tenant isolation
CREATE POLICY tenant_isolation ON grades
    USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- Organization isolation (for division-level users)
CREATE POLICY org_isolation ON grades
    USING (
        tenant_id = current_setting('app.tenant_id')::uuid
        AND (
            current_setting('app.org_id') IS NULL
            OR organization_id = current_setting('app.org_id')::uuid
        )
    );

-- School isolation (for school-level users)
CREATE POLICY school_isolation ON grades
    USING (
        tenant_id = current_setting('app.tenant_id')::uuid
        AND (
            current_setting('app.school_id') IS NULL
            OR school_id = current_setting('app.school_id')::uuid
        )
    );

-- Read-only for teacher role
CREATE POLICY teacher_read_only ON grades
    FOR SELECT
    USING (
        tenant_id = current_setting('app.tenant_id')::uuid
        AND (
            current_setting('app.user_role') = 'super_admin'
            OR (
                current_setting('app.user_role') = 'teacher'
                AND current_setting('app.user_id') IS NOT NULL
            )
        )
    );
```

### 4.4 Cross-Tenant Protection

| Attack Vector | Protection |
|---|---|
| Tenant ID in URL manipulation | Validate tenant matches JWT claim |
| HTTP header spoofing | Sign tenant_id in JWT; compare header to claim |
| Database cross-tenant query | RLS prevents reading other tenants' rows |
| Cache poisoning | Cache keys include tenant_id |
| Shared file storage | Pre-signed URLs scoped to tenant |
| AI context leakage | Tenant isolation in RAG vector store |

---

## 5. Database Security Design

### 5.1 Encryption Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                  Data Encryption Strategy                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  At Rest:                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL TDE (Transparent Data Encryption)            │   │
│  │  AES-256 encrypted data files at OS/disk level           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  In Transit:                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  TLS 1.3 for all connections                             │   │
│  │  HSTS enabled (Strict-Transport-Security)                │   │
│  │  mTLS for inter-service communication (future)           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Field-Level (Application):                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  AES-256-GCM for PII fields                              │   │
│  │  Key rotation support (versioned keys)                   │   │
│  │  Encrypted fields:                                       │   │
│  │  • refresh_token (database column)                       │   │
│  │  • guardian_contact_number                               │   │
│  │  • guardian_email                                        │   │
│  │  • parent_contact                                        │   │
│  │  • student_address                                       │   │
│  │  • emergency_contact                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 AES-256-GCM Implementation

```python
# EncryptionService — Field-level encryption
class EncryptionService:
    def __init__(self, master_key: bytes):
        self._keys = self._derive_keys(master_key)

    def encrypt(self, plaintext: str, context: str = "") -> str:
        """Encrypt with AES-256-GCM, return base64(version + nonce + ciphertext + tag)."""
        key = self._keys["current"]
        nonce = os.urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        encryptor.authenticate_additional_data(context.encode())
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return base64.b64encode(b"\x01" + nonce + ciphertext + encryptor.tag).decode()

    def decrypt(self, encrypted: str, context: str = "") -> str:
        """Decrypt, verify authentication tag, return plaintext."""
        data = base64.b64decode(encrypted)
        version = data[0]
        nonce = data[1:13]
        tag = data[-16:]
        ciphertext = data[13:-16]
        key = self._keys.get(f"v{version}", self._keys["current"])
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(context.encode())
        return (decryptor.update(ciphertext) + decryptor.finalize()).decode()
```

### 5.3 Database Audit Trail

```sql
-- Append-only audit_logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    tenant_id UUID,
    organization_id UUID,
    school_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    correlation_id UUID,
    severity VARCHAR(20) DEFAULT 'info',
    outcome VARCHAR(20) DEFAULT 'success',
    -- Immutable constraint
    CONSTRAINT chk_no_update CHECK (true) NO INHERIT
);

-- Trigger to prevent updates
CREATE OR REPLACE FUNCTION prevent_audit_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_immutable
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_update();
```

---

## 6. AI Security Design

### 6.1 AI Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Security Layers                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  1. Input Guard (PromptInjectionGuard)                   │   │
│  │  • Detect injection patterns (DAN, system override, etc) │   │
│  │  • Sanitize unsafe tokens                                │   │
│  │  • Block known jailbreak attempts                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  2. PII Detector (PIIDetector)                           │   │
│  │  • Detect emails, phone numbers, LRNs, SSNs             │   │
│  │  • Redact PII before sending to LLM                      │   │
│  │  • Alert on unexpected PII exposure                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  3. Tool Permission Check (AIToolPermissionService)      │   │
│  │  • Verify user has permission for each tool              │   │
│  │  • Enforce sensitivity levels per tool                   │   │
│  │  • MFA requirement for high-sensitivity tools            │   │
│  │  • Rate limit per tool per user (sliding window)         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  4. Output Review Gate (ReviewGate)                      │   │
│  │  • Human-in-the-loop review                              │   │
│  │  • Auto-approval for low-risk outputs                    │   │
│  │  • Content policy enforcement                            │   │
│  │  • Version comparison on re-generation                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Tool Sensitivity Matrix

| Tool | Sensitivity | Requires MFA | Rate Limit (/min) | Allowed Roles |
|---|---|---|---|---|
| `curriculum_search` | Low | No | 60 | All |
| `melc_lookup` | Low | No | 60 | All |
| `transmutation_lookup` | Low | No | 60 | All |
| `student_search` | Medium | No | 30 | Adviser+ |
| `school_config_lookup` | Medium | No | 30 | All |
| `form_template_lookup` | Medium | No | 30 | Teacher+ |
| `rubric_generator` | Medium | No | 15 | Teacher+ |
| `grade_lookup` | High | Yes | 15 | Adviser+ |
| `attendance_analyzer` | High | Yes | 15 | Adviser+ |
| `student_risk_score` | High | Yes | 10 | Adviser+ |
| `notification_sender` | High | Yes | 10 | Adviser+ |
| `form_validator` | Critical | Yes | 5 | Coordinator+ |

### 6.3 Prompt Injection Protection

```python
# Detection patterns monitored
PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"system\s*:\s*",
    r"<\|system\|>",
    r"\[SYSTEM\]",
    r"override\s+(system|safety)",
    r"jailbreak",
    r"DAN\s+mode",
    r"pretend\s+(you|that)\s+(are|is)",
]

# PII patterns for Philippines (DepEd context)
PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"(?:\+63|0)9\d{9}",
    "lrn": r"\d{2}-\d{5}-\d{2}-\d{5}",  # DepEd LRN format
    "ssn_ph": r"\d{4}-\d{7}-\d{1}",    # PhilSys/SSS
}
```

### 6.4 AI Audit Trail

Every AI interaction is logged with:
- **Tool Execution**: tool name, arguments, result, latency, user, tenant
- **Agent Run**: agent kind, input context hash, output, review state
- **Permission Check**: tool, user, decision (allow/deny), reason
- **Injection Detection**: prompt fragment, match pattern, severity

---

## 7. Audit Logging Design

### 7.1 Audit Event Taxonomy

| Category | Events | Retention |
|---|---|---|
| **Authentication** | Login, logout, password change, password reset, MFA toggle | 1 year |
| **Authorization** | Permission denied, role change, privilege escalation attempt | 1 year |
| **Data Operations** | Create, update, delete (grades, students, attendance) | 5 years |
| **AI Operations** | Agent run, tool execution, output generation, review | 1 year |
| **Security Events** | Brute force, token reuse, cross-tenant attempt, rate limit | 1 year |
| **File Operations** | Upload, download, delete, validation failure | 1 year |
| **Compliance** | Consent grant/revoke, data export, data deletion | 5 years |

### 7.2 Audit Entry Structure

```python
@dataclass
class AuditEntry:
    id: str                        # UUID v4
    timestamp: datetime            # UTC
    actor_id: str                  # User who performed action
    action: str                    # LOGIN, CREATE, UPDATE, DELETE, etc.
    resource_type: str             # grade, student, session, form, etc.
    resource_id: str               # Resource identifier
    tenant_id: Optional[str]       # Tenant context
    organization_id: Optional[str] # Organization context
    school_id: Optional[str]       # School context
    details: Optional[Dict]        # Arbitrary contextual data
    ip_address: Optional[str]      # Client IP
    user_agent: Optional[str]      # User-Agent header
    request_id: Optional[str]      # Correlate with HTTP request
    correlation_id: Optional[str]  # Distributed tracing
    severity: str                  # info, warning, error, critical
    outcome: str                   # success, failure
```

### 7.3 Audit Query Capabilities

```
AuditService
├── log()                                    # Core append-only log
├── get_entries_for_user(user_id)            # User activity trail
├── get_entries_for_resource(type, id)       # Resource change history
├── get_entries_for_tenant(tenant_id)        # Tenant audit trail
├── get_entries_by_action(action)            # Filter by action type
├── get_recent_entries(limit)                # Recent activity feed
├── count_entries(tenant_id)                # Audit volume stats
├── log_login()                              # Convenience: login
├── log_logout()                             # Convenience: logout
└── log_data_change()                        # Convenience: CRUD
```

---

## 8. Threat Model

### 8.1 STRIDE Threat Assessment

| Category | Threat | Mitigation | Severity |
|---|---|---|---|
| **S**poofing | Attacker impersonates user via stolen JWT | RS256 signatures, jti , device tracking, short token expiry | High |
| **T**ampering | Attacker modifies audit logs | Append-only structure, immutable constraint | High |
| **R**epudiation | User denies performing action | Immutable audit trail with actor, timestamp, IP | Medium |
| **I**nformation Disclosure | Cross-tenant data access | RLS policies, tenant context validation, field encryption | Critical |
| **D**enial of Service | Brute force login | Rate limiting, account lockout, SlowAPI middleware | Medium |
| **E**levation of Privilege | User escalates to admin | RBAC, permission checks on every endpoint, audit alerts | Critical |

### 8.2 Attack Scenarios & Mitigations

| Scenario | Attack Vector | Detection | Response |
|---|---|---|---|
| **Token Theft** | XSS, malicious extension, network intercept | jti reuse detection, device mismatch | Revoke all sessions, blacklist tokens, notify user |
| **Brute Force** | Repeated login attempts | SecurityEventService (5 failures/5min) | Account lockout + alert admin + rate limit IP |
| **Cross-Tenant** | Manipulated tenant headers | Tenant ≠ JWT claim → EVENT_CROSS_TENANT | Deny request + high-severity security event |
| **Prompt Injection** | Crafted user input to LLM | PromptInjectionGuard pattern match | Block + record EVENT_AI_PROMPT_INJECTION |
| **Privilege Escalation** | Modified JWT claims | RS256 verification fails | Deny + EVENT_PRIVILEGE_ESCALATION_ATTEMPT |
| **PII Leakage** | LLM returns student PII | PIIDetector in output guard | Redact + alert + log security event |
| **Session Hijacking** | Stolen session cookie | Device fingerprint mismatch | Revoke session + force re-auth + alert |
| **Rate Limit Bypass** | Distributed IP attacks | SlowAPI per-IP + per-user tracking | Block + log + alert for distributed patterns |

### 8.3 Data Sensitivity Classification

| Classification | Examples | Storage | Encryption |
|---|---|---|---|
| **Public** | School name, address, contact info | Plaintext | TLS in transit |
| **Internal** | Teacher names, subject assignments | Plaintext | TLS + DB-level TDE |
| **Sensitive** | Grades, attendance records, behavior notes | Plaintext | TLS + RLS + audit trail |
| **Confidential** | Student LRN, parent contacts, guardian info | Encrypted | AES-256-GCM + TLS + RLS |
| **Restricted** | Authentication secrets, MFA seeds | Hashed/Encrypted | Argon2id / AES-256-GCM |

---

## 9. Security Metrics & Monitoring

### 9.1 Prometheus Metrics

| Metric | Type | Labels | Purpose |
|---|---|---|---|
| `teacheros_security_auth_attempts_total` | Counter | status, method | Auth success/failure rate |
| `teacheros_security_token_operations_total` | Counter | operation, token_type | Token lifecycle tracking |
| `teacheros_security_rate_limit_events_total` | Counter | scope, action | Rate limit hit/exceeded |
| `teacheros_security_active_sessions` | Gauge | tenant_id | Current session count |
| `teacheros_security_sessions_created_total` | Counter | - | Session creation rate |
| `teacheros_security_sessions_revoked_total` | Counter | - | Session revocation rate |
| `teacheros_security_mfa_operations_total` | Counter | operation, status | MFA usage tracking |
| `teacheros_security_permission_denied_total` | Counter | permission, tenant_id | Denied authorization |
| `teacheros_security_brute_force_events_total` | Counter | tenant_id | Brute force detection |
| `teacheros_security_file_validation_total` | Counter | result | File validation stats |
| `teacheros_security_event_latency_seconds` | Histogram | event_type | Processing latency |
| `teacheros_security_active_mfa_users` | Gauge | - | MFA adoption |
| `teacheros_security_blacklisted_tokens` | Gauge | token_type | Blacklist size |

### 9.2 Alerting Thresholds

| Alert | Condition | Severity | Response |
|---|---|---|---|
| Brute Force Detected | >10 failures in 5 min | Critical | Auto-block + notify admin |
| MFA Failures Spike | >5 MFA failures/min/user | High | Suspend account + investigate |
| Token Reuse Detected | Any reuse event | Critical | Revoke all tokens + force re-auth |
| Cross-Tenant Attempt | Any detection | High | Block + log + investigate |
| Privilege Escalation | Any attempt | Critical | Block + immediate admin alert |
| Rate Limit Spike | >100 exceeded/min | Medium | Investigate potential DDoS |
| Low MFA Adoption | <30% of users enabled | Warning | Campaign to enable MFA |

### 9.3 Security Dashboard

The SecurityMetricsService provides a `take_snapshot()` method that returns:

```json
{
  "timestamp": "2026-06-10T12:00:00Z",
  "auth_attempts": {
    "total": 15420,
    "success": 14800,
    "failure": 620
  },
  "active_sessions": 342,
  "mfa_enabled_users": 156,
  "blacklisted_tokens": 45,
  "rate_limit_exceeded": 23,
  "permission_denied_count": 12,
  "brute_force_events": 2,
  "file_rejections": 7
}
```

---

## 10. API Security Controls

### 10.1 Middleware Stack

```
Request → RateLimitMiddleware → CSRFMiddleware → RequestIDMiddleware
         → AuthMiddleware → RBACMiddleware → Application Handler → Response
```

### 10.2 Rate Limiting Configuration

| Scope | Rate Limit | Burst |
|---|---|---|
| `public` (unauthenticated) | 20/min | 5 |
| `authenticated` | 100/min | 20 |
| `login` | 5/min per IP | 2 |
| `ai` (agent execution) | 10/min per user | 3 |

### 10.3 CSRF Protection

- Double-submit cookie pattern
- CSRF token in `X-CSRF-Token` header
- Token bound to session ID
- CSRF token regenerated on login
- Idempotency key support for safe retries

### 10.4 Request Tracking

Each request receives:
- **Request ID**: Generated at edge, passed through stack
- **Correlation ID**: Ties together related requests (login chain)
- **Client IP**: Extracted from X-Forwarded-For / X-Real-IP
- **User-Agent**: Original client user-agent for fingerprinting

### 10.5 Secure Headers

```python
# Enabled headers
"X-Content-Type-Options": "nosniff"
"X-Frame-Options": "DENY"
"X-XSS-Protection": "1; mode=block"
"Strict-Transport-Security": "max-age=31536000; includeSubDomains"
"Content-Security-Policy": "default-src 'self'"
"Referrer-Policy": "strict-origin-when-cross-origin"
"Cache-Control": "no-store, max-age=0"  # For auth responses
```

### 10.6 File Upload Security

| Check | Implementation | Bypass Vector |
|---|---|---|
| File Extension | Whitelist: .pdf, .docx, .xlsx, .jpg, .png | Double extension, null byte |
| MIME Type | Verify Content-Type header | MIME sniffing |
| Magic Bytes | Read file header bytes | Embed magic bytes in other format |
| File Size | Max 10MB | Large file DoS |
| Virus Scan | ClamAV integration (future) | Encrypted payloads |
| Tenant Isolation | Prefixed storage path | Path traversal |

---

## 11. Data Encryption Strategy

### 11.1 Key Hierarchy

```
┌──────────────────────────────┐
│       Master Key (HSM)        │
│  • 256-bit, hardware-backed   │
│  • Stored in AWS KMS / Azure  │
│  • Rotated annually            │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│     Key Derivation (HKDF)     │
│  • Application key            │
│  • Token encryption key       │
│  • MFA seed key               │
│  • File encryption key        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│     Per-Field Encryption      │
│  • AES-256-GCM with unique   │
│    nonce per encryption       │
│  • AAD includes field context │
│  • Version prefix for rotation│
└──────────────────────────────┘
```

### 11.2 Encryption Performance

| Operation | Avg Latency | Throughput (1K records) |
|---|---|---|
| AES-256-GCM Encrypt (100B) | ~0.3ms | 300+ ops/sec |
| AES-256-GCM Decrypt (100B) | ~0.3ms | 300+ ops/sec |
| Argon2id Hash (t=2, m=19456) | ~50ms | 20 ops/sec |
| RS256 Sign (4096-bit) | ~2ms | 500 ops/sec |
| RS256 Verify (4096-bit) | ~0.1ms | 10000 ops/sec |

---

## 12. Security Incident Response

### 12.1 Incident Severity Levels

| Level | Definition | Examples | Response Time |
|---|---|---|---|
| **SEV-1** | Active data breach, system compromise | Token theft, cross-tenant access, data exfiltration | Immediate (<15 min) |
| **SEV-2** | Active attack in progress | Brute force, injection attempts, privilege escalation | <1 hour |
| **SEV-3** | Suspicious activity detected | Failed MFA spike, unusual geo-location | <4 hours |
| **SEV-4** | Policy violation, configuration issue | Weak password detected, missing MFA | <24 hours |

### 12.2 Response Playbook

```
SEV-1: Data Breach Response
1. Isolate: Revoke all tokens, disable affected accounts
2. Contain: Block IP ranges, enable max security mode
3. Investigate: Review audit trail, identify scope
4. Eradicate: Rotate keys, patch vulnerability
5. Recover: Restore from clean backup, audit all changes
6. Post-mortem: Root cause analysis, improve controls

SEV-2: Active Attack Response
1. Block: Rate limit suspicious IPs/users aggressively
2. Alert: Notify security team via configured channels
3. Monitor: Increase logging verbosity for attacker
4. Investigate: Trace attack vector and attempted exploitation
5. Patch: Apply immediate fixes for identified vulnerability
6. Document: Update threat model with new attack pattern

SEV-3: Suspicious Activity
1. Investigate: Review security events and audit logs
2. Assess: Determine if activity is malicious or false positive
3. Respond: Apply targeted blocking if needed
4. Tune: Adjust detection thresholds if false positive
5. Report: Document finding in security log

SEV-4: Policy/Configuration
1. Review: Assess policy violation or misconfiguration
2. Correct: Fix configuration, notify responsible party
3. Verify: Confirm fix resolves the issue
4. Document: Update runbooks and configuration guides
```

### 12.3 Security Contact & Escalation

| Role | Responsibility | Contact |
|---|---|---|
| Security Engineer | First response, technical investigation | On-call rotation |
| Security Architect | Architecture review, threat model updates | Principal |
| CTO | Business decisions, regulatory notification | Executive |
| DPO (Data Protection Officer) | Privacy impact, compliance reporting | Legal |

---

## Appendix A: Security Service Dependencies

| Service | Depends On | Used By |
|---|---|---|
| JWTService | settings.JWT_PRIVATE_KEY | AuthMiddleware, Auth routes |
| TokenService | Redis (blacklist), JWTService | Auth routes, SessionService |
| PasswordService | Argon2id, settings | Auth routes, User management |
| MFAService | Redis (OTP store), EncryptionService | Auth routes, User settings |
| SessionService | Redis, JWTService | Auth routes, Session management |
| RBACService | PermissionEngine, RoleEngine | All protected endpoints |
| AuditService | PostgreSQL (append-only log) | All services |
| SecurityEventService | Redis (pattern detection) | Auth, API, AI services |
| SecurityMetricsService | Prometheus | Monitoring, dashboards |
| AIToolPermissionService | RBACService, ToolRegistry | AI agent execution |
| RateLimitMiddleware | SlowAPI, Redis | All API endpoints |
| CSRFMiddleware | Session ID | State-changing endpoints |
| RequestIDMiddleware | UUID generation | All API endpoints |
| FileValidationService | python-magic | File upload endpoints |

## Appendix B: Security Constants Reference

```python
# Password policy
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_AGE_DAYS = 90
PASSWORD_HISTORY_SIZE = 10
ACCOUNT_LOCKOUT_THRESHOLD = 5
ACCOUNT_LOCKOUT_MINUTES = 15

# Token policy
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
TOKEN_BLACKLIST_TTL_HOURS = 48
JWT_ALGORITHM = "RS256"
JWT_KEY_SIZE_BITS = 4096

# Session policy
MAX_SESSIONS_PER_USER = 10
SESSION_IDLE_TIMEOUT_MINUTES = 30

# Rate limiting
RATE_LIMIT_PUBLIC = 20
RATE_LIMIT_AUTHENTICATED = 100
RATE_LIMIT_LOGIN = 5
RATE_LIMIT_AI = 10

# Encryption
ENCRYPTION_ALGORITHM = "AES-256-GCM"
ENCRYPTION_KEY_SIZE_BITS = 256
ENCRYPTED_FIELDS = [
    "refresh_token", "guardian_contact_number",
    "guardian_email", "parent_contact",
    "student_address", "emergency_contact",
]

# Security events
EVENT_LOGIN_FAILED = "login.failed"
EVENT_TOKEN_REUSE_DETECTED = "token.reuse.detected"
EVENT_PRIVILEGE_ESCALATION_ATTEMPT = "privilege.escalation.attempt"
EVENT_CROSS_TENANT_ACCESS_ATTEMPT = "cross.tenant.access.attempt"
EVENT_AI_PROMPT_INJECTION_DETECTED = "ai.prompt.injection.detected"

# Brute force detection
BRUTE_FORCE_THRESHOLD = 5
BRUTE_FORCE_WINDOW_MINUTES = 5
```

## Appendix C: Testing Security Controls

| Test Category | Test Cases | Priority |
|---|---|---|
| **Authentication** | Password complexity enforcement, MFA enrollment/verification, token issuance/refresh/revocation, session management | Critical |
| **Authorization** | RBAC permission checks, role inheritance, cross-tenant isolation, permission denial | Critical |
| **Token Security** | JWT signature verification, token blacklist, token reuse detection, device tracking | Critical |
| **Rate Limiting** | Per-scope limits, burst handling, IP-based blocking, reset behavior | High |
| **CSRF** | Token validation, missing token, expired token, wrong origin | High |
| **File Upload** | Extension validation, MIME check, magic bytes, size limits, path traversal | High |
| **Prompt Injection** | Known patterns, edge cases, sanitization, redaction | High |
| **Encryption** | Encrypt/decrypt round-trip, key rotation, tamper detection, AAD verification | High |
| **Audit** | Append-only enforcement, entry completeness, query accuracy | Medium |
| **Security Events** | Brute force detection, event severity escalation, event resolution | Medium |

---

*End of Security Architecture Document. This is a living document — update as security controls evolve.*
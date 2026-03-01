# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

> **Note:** This project is pre-release. The table above reflects the current development
> version and will be updated when the first stable release is published to PyPI.

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

To report a vulnerability, use GitHub's private vulnerability reporting feature:

1. Navigate to the [Security tab](https://github.com/Alberto-Codes/adk-secure-sessions/security) of this repository
2. Click **"Report a vulnerability"**
3. Fill in the details of the vulnerability

This creates a private security advisory that only repository maintainers can see.

### What to Include

- A description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Any relevant logs, screenshots, or proof-of-concept code
- Your assessment of severity (Critical, High, Medium, Low)

## Response Timeline

| Severity | Acknowledgment | Assessment | Fix Target |
|----------|---------------|------------|------------|
| Critical | 48 hours      | 7 days     | 30 days    |
| High     | 48 hours      | 14 days    | 60 days    |
| Medium   | 7 days        | 30 days    | 90 days    |
| Low      | 14 days       | 60 days    | Next release |

- **Acknowledgment**: You will receive confirmation that your report was received.
- **Assessment**: The maintainer will evaluate severity and determine the fix approach.
- **Fix Target**: A patch release addressing the vulnerability.

All timelines are best-effort targets for a solo-maintainer project.

## Cryptographic Approach

This library delegates symmetric encryption and authentication to the
[`cryptography`](https://cryptography.io/) Python library (Fernet). Key derivation
from passphrases uses Python's standard-library `hashlib.pbkdf2_hmac`. No custom
cryptographic primitives are implemented.

**Current encryption scheme:**

- **Algorithm**: Fernet (AES-128-CBC + HMAC-SHA256)
- **Key derivation**: PBKDF2-HMAC-SHA256
- **Envelope format**: Self-describing binary header (`[version][backend_id][ciphertext]`)
  for key rotation and audit support

Design rationale is documented in
[ADR-003: Field-Level Encryption by Default](docs/adr/ADR-003-field-level-encryption.md).

## Scope

This library provides **encryption at rest** for Google ADK session state data.

### What This Library Protects

- Session state fields are encrypted before database persistence
- All encrypted data uses a self-describing envelope format for auditability
- Wrong-key decryption always raises an explicit error (no silent failures)

### What This Library Does NOT Protect

- **Data in transit** — transport-layer encryption (TLS) is the responsibility of your
  application infrastructure
- **Key management** — generating, storing, and rotating encryption keys is the
  responsibility of the deployer
- **Database access controls** — file-system permissions and network access to the
  SQLite database are outside this library's scope
- **Application-level authorization** — this library encrypts data, it does not enforce
  who can access it

### Compliance Note

This library is designed to support encryption-at-rest requirements for regulated
environments (HIPAA, SOC 2, PCI-DSS). It does **not** provide or claim certification
for any compliance framework. Certification is the responsibility of the deploying
organization.

# Security Policy

## Supported Versions

We take security seriously and provide security updates for the following versions:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 1.0.x   | :white_check_mark: | Active support, security updates |
| < 1.0   | :x:                | No longer supported |

## Security Model

The MCP Optimizer Framework implements a defense-in-depth security model with multiple layers:

### 1. Sandbox Isolation

All code execution occurs within isolated sandboxes with strict resource limits:

- **Docker Sandbox** (Production default):
  - Seccomp filtering of system calls
  - AppArmor MAC enforcement
  - Network isolation (no network access)
  - Read-only root filesystem
  - No privilege escalation
  - Resource limits (CPU, memory, processes)

- **Resource Limits**:
  - CPU: 0.5 cores max
  - Memory: 512MB max (configurable)
  - Processes: 50 max
  - File handles: 100 max
  - Execution time: 30 seconds max
  - Disk: 100MB max

### 2. Input Validation

- All user inputs are validated before execution
- Parameters are sanitized to prevent injection attacks
- JSON Schema validation for structured inputs
- Token limits prevent oversized requests

### 3. Principle of Least Privilege

- Processes run with minimal permissions
- No root access in containers
- Capability-based security model
- Explicit permission requirements

### 4. Audit Logging

- All operations are logged with structured logging
- Failed security checks are recorded
- Audit trail for compliance
- Metrics for security monitoring

### 5. Fail-Closed Design

- Security failures result in operation denial
- Explicit opt-in for reduced security
- No fallback to unsafe execution
- Clear error messages for security violations

## Reporting a Vulnerability

**DO NOT** open a public GitHub issue for security vulnerabilities.

### How to Report

1. **Email**: Send details to **rhart696@gmail.com**
2. **Subject**: Include "SECURITY" in the subject line
3. **Details**: Provide as much information as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)
   - Your contact information

### What to Expect

| Timeline | Action |
|----------|--------|
| 24 hours | Initial acknowledgment of your report |
| 48 hours | Assessment of severity and impact |
| 7 days   | Initial patch development (for critical issues) |
| 14 days  | Security advisory publication |
| 30 days  | Full disclosure (coordinated with reporter) |

### Response Process

1. **Acknowledgment**: We'll confirm receipt within 24 hours
2. **Assessment**: We'll assess severity using CVSS 3.1
3. **Development**: We'll develop and test a fix
4. **Notification**: We'll notify you before public disclosure
5. **Release**: We'll release a security update
6. **Disclosure**: We'll publish a security advisory

### Severity Levels

We use CVSS 3.1 scoring:

- **Critical** (9.0-10.0): Remote code execution, privilege escalation
- **High** (7.0-8.9): Data exposure, sandbox escape
- **Medium** (4.0-6.9): DoS, information disclosure
- **Low** (0.1-3.9): Minor information leak, edge cases

## Security Best Practices

### For Users

1. **Always use sandboxing**:
   ```python
   from mcp_optimizer import CodeExecutor, FeatureFlags

   # ✅ Good: Sandboxing enabled (default)
   flags = FeatureFlags(enable_sandbox=True)

   # ❌ Bad: Sandboxing disabled
   flags = FeatureFlags(enable_sandbox=False)  # Only for development!
   ```

2. **Configure resource limits**:
   ```python
   from mcp_optimizer import SecureSandbox

   sandbox = SecureSandbox(
       enabled=True,
       backend="docker"  # Most secure option
   )

   result = await sandbox.execute(
       code=code,
       timeout=30,      # Maximum execution time
       memory_mb=512    # Maximum memory usage
   )
   ```

3. **Use hybrid mode for testing**:
   ```python
   # Start with MCP_ONLY for compatibility
   flags = FeatureFlags(execution_mode=ExecutionMode.MCP_ONLY)

   # Gradually enable code execution
   flags = FeatureFlags(execution_mode=ExecutionMode.HYBRID)

   # Full code execution after validation
   flags = FeatureFlags(execution_mode=ExecutionMode.CODE_EXECUTION)
   ```

4. **Monitor security metrics**:
   ```python
   # Enable metrics and telemetry
   flags = FeatureFlags(
       enable_metrics=True,
       enable_telemetry=True
   )

   # Monitor security events
   metrics.increment("sandbox_violation")
   metrics.increment("execution_timeout")
   ```

5. **Keep dependencies updated**:
   ```bash
   # Regularly update dependencies
   pip install --upgrade mcp-optimizer-framework

   # Check for security advisories
   pip-audit
   ```

### For Developers

1. **Never disable sandboxing in production**
2. **Validate all inputs before processing**
3. **Use type hints and validation (Pydantic)**
4. **Follow principle of least privilege**
5. **Enable all security features**
6. **Regular security audits of custom code**
7. **Use secrets management for credentials**
8. **Implement rate limiting**
9. **Monitor for suspicious activity**
10. **Keep Docker images updated**

### Docker Security

```yaml
# docker-compose.yml security best practices
services:
  mcp-optimizer:
    image: mcp-optimizer:latest
    security_opt:
      - no-new-privileges:true
      - seccomp=/etc/docker/seccomp-mcp.json
      - apparmor=docker-mcp
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    read_only: true
    networks:
      - isolated
    mem_limit: 512m
    cpus: 0.5
```

### Environment Variables

Never commit secrets to version control:

```bash
# ✅ Good: Use environment variables
export SENTRY_API_KEY="..."
export GITHUB_TOKEN="..."

# ❌ Bad: Hardcoded secrets
api_key = "sk_live_abc123..."
```

## Security Features

### Current Implementation

- ✅ Docker-based sandbox isolation
- ✅ Seccomp filtering
- ✅ AppArmor profiles
- ✅ Resource limits (CPU, memory, processes)
- ✅ Network isolation
- ✅ Read-only filesystems
- ✅ Structured audit logging
- ✅ Metrics and monitoring
- ✅ Input validation
- ✅ Token limits

### Planned Enhancements

- 🔄 Firecracker microVM support
- 🔄 WebAssembly (WASM) sandbox
- 🔄 Hardware security module (HSM) integration
- 🔄 Kubernetes security context support
- 🔄 Rate limiting per tenant
- 🔄 Anomaly detection
- 🔄 Security scanning automation

## Known Issues

None currently reported.

## Security Contacts

- **Email**: rhart696@gmail.com
- **GitHub**: [@rhart696](https://github.com/rhart696)
- **Security Advisories**: https://github.com/rhart696/mcp-optimizer-framework/security/advisories

## Acknowledgments

We thank the following security researchers for responsible disclosure:

- (None yet - be the first!)

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Python Security](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## Compliance

This project follows industry-standard security practices:

- OWASP Application Security Verification Standard (ASVS)
- CIS Docker Benchmark
- NIST SP 800-53 (selected controls)
- Principle of least privilege
- Defense in depth
- Fail-closed design

---

**Last Updated**: 2024-11-24
**Version**: 1.0.0

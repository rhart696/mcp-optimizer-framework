# Deployment Guide

Production deployment guide for MCP Optimizer Framework v1.0.0.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment Options](#deployment-options)
- [Monitoring](#monitoring)
- [Security Hardening](#security-hardening)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

## Overview

The MCP Optimizer Framework is designed for production deployment with multiple sandbox backends and comprehensive monitoring. This guide covers deployment strategies for various environments.

### Deployment Architecture

```
┌─────────────────────────────────────────────┐
│           Load Balancer (nginx)              │
└───────────────┬─────────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
┌───────▼──────┐  ┌─────▼────────┐
│   App Node 1  │  │  App Node 2  │
│ (Framework)   │  │ (Framework)  │
└───────┬──────┘  └──────┬───────┘
        │                │
        └────────┬───────┘
                 │
        ┌────────▼────────┐
        │  Redis Cluster   │
        │  (Session State) │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │   Prometheus     │
        │    (Metrics)     │
        └─────────────────┘
```

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 22.04 LTS recommended)
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ recommended
- **Disk**: 50GB+ available space
- **Python**: 3.8 or higher

### Required Software

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and dependencies
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Install Docker (for Docker sandbox backend)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Redis (for session management)
sudo apt-get install -y redis-server

# Install monitoring tools
sudo apt-get install -y prometheus prometheus-node-exporter
```

### Optional Software

```bash
# For gVisor sandbox (maximum security)
curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/apt/sources.list.d/gvisor.list > /dev/null
sudo apt-get update && sudo apt-get install -y runsc

# For Firecracker sandbox
wget https://github.com/firecracker-microvm/firecracker/releases/download/v1.4.0/firecracker-v1.4.0-x86_64.tgz
tar xvf firecracker-v1.4.0-x86_64.tgz
sudo mv release-v1.4.0-x86_64/firecracker-v1.4.0-x86_64 /usr/local/bin/firecracker
```

## Installation

### 1. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/rhart696/mcp-optimizer-framework.git
cd mcp-optimizer-framework
sudo chown -R $USER:$USER .
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Install package
pip install -e .

# Verify installation
mcp-optimizer --version
```

### 4. Create System User (Production)

```bash
# Create dedicated user
sudo useradd -r -s /bin/false -d /opt/mcp-optimizer-framework mcp-optimizer

# Set ownership
sudo chown -R mcp-optimizer:mcp-optimizer /opt/mcp-optimizer-framework

# Create log directory
sudo mkdir -p /var/log/mcp-optimizer
sudo chown mcp-optimizer:mcp-optimizer /var/log/mcp-optimizer
```

## Configuration

### 1. Environment Variables

Create `/opt/mcp-optimizer-framework/.env`:

```bash
# Execution Mode
EXECUTION_MODE=hybrid

# Sandbox Configuration
SANDBOX_BACKEND=docker
SANDBOX_ENABLED=true
MAX_EXECUTION_TIME=30
MAX_MEMORY_MB=512

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_secure_password_here
CACHE_TTL_SECONDS=300

# Metrics Configuration
ENABLE_METRICS=true
PROMETHEUS_PORT=9090

# Telemetry Configuration
ENABLE_TELEMETRY=true
TELEMETRY_ENDPOINT=https://telemetry.example.com

# Security
ENABLE_SANDBOX=true
MAX_TOKENS_PER_REQUEST=1000
CONTEXT_SIZE_LIMIT_KB=100

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 2. Redis Configuration

Edit `/etc/redis/redis.conf`:

```bash
# Bind to localhost only
bind 127.0.0.1

# Require password
requirepass your_secure_password_here

# Enable persistence
save 900 1
save 300 10
save 60 10000

# Set max memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Enable AOF for durability
appendonly yes
appendfsync everysec
```

Restart Redis:

```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 3. Docker Sandbox Configuration

Create seccomp profile at `/etc/docker/seccomp-mcp.json`:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_X86",
    "SCMP_ARCH_X32"
  ],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "close", "stat", "fstat", "lstat",
        "poll", "lseek", "mmap", "mprotect", "munmap", "brk",
        "rt_sigaction", "rt_sigprocmask", "rt_sigreturn", "ioctl",
        "pread64", "pwrite64", "readv", "writev", "access", "pipe",
        "select", "sched_yield", "mremap", "msync", "mincore",
        "madvise", "shmget", "shmat", "shmctl", "dup", "dup2",
        "pause", "nanosleep", "getitimer", "alarm", "setitimer",
        "getpid", "sendfile", "socket", "connect", "accept", "sendto",
        "recvfrom", "sendmsg", "recvmsg", "shutdown", "bind", "listen",
        "getsockname", "getpeername", "socketpair", "setsockopt",
        "getsockopt", "clone", "fork", "vfork", "execve", "exit",
        "wait4", "kill", "uname", "semget", "semop", "semctl",
        "shmdt", "msgget", "msgsnd", "msgrcv", "msgctl", "fcntl",
        "flock", "fsync", "fdatasync", "truncate", "ftruncate",
        "getdents", "getcwd", "chdir", "fchdir", "rename", "mkdir",
        "rmdir", "creat", "link", "unlink", "symlink", "readlink",
        "chmod", "fchmod", "chown", "fchown", "lchown", "umask",
        "gettimeofday", "getrlimit", "getrusage", "sysinfo", "times",
        "ptrace", "getuid", "syslog", "getgid", "setuid", "setgid",
        "geteuid", "getegid", "setpgid", "getppid", "getpgrp",
        "setsid", "setreuid", "setregid", "getgroups", "setgroups",
        "setresuid", "getresuid", "setresgid", "getresgid", "getpgid",
        "setfsuid", "setfsgid", "getsid", "capget", "capset",
        "rt_sigpending", "rt_sigtimedwait", "rt_sigqueueinfo",
        "rt_sigsuspend", "sigaltstack", "utime", "mknod", "uselib",
        "personality", "ustat", "statfs", "fstatfs", "sysfs",
        "getpriority", "setpriority", "sched_setparam",
        "sched_getparam", "sched_setscheduler", "sched_getscheduler",
        "sched_get_priority_max", "sched_get_priority_min",
        "sched_rr_get_interval", "mlock", "munlock", "mlockall",
        "munlockall", "vhangup", "modify_ldt", "pivot_root",
        "_sysctl", "prctl", "arch_prctl", "adjtimex", "setrlimit",
        "chroot", "sync", "acct", "settimeofday", "mount", "umount2",
        "swapon", "swapoff", "reboot", "sethostname", "setdomainname",
        "iopl", "ioperm", "create_module", "init_module",
        "delete_module", "get_kernel_syms", "query_module", "quotactl",
        "nfsservctl", "getpmsg", "putpmsg", "afs_syscall",
        "tuxcall", "security", "gettid", "readahead", "setxattr",
        "lsetxattr", "fsetxattr", "getxattr", "lgetxattr",
        "fgetxattr", "listxattr", "llistxattr", "flistxattr",
        "removexattr", "lremovexattr", "fremovexattr", "tkill",
        "time", "futex", "sched_setaffinity", "sched_getaffinity",
        "set_thread_area", "io_setup", "io_destroy", "io_getevents",
        "io_submit", "io_cancel", "get_thread_area", "lookup_dcookie",
        "epoll_create", "epoll_ctl_old", "epoll_wait_old",
        "remap_file_pages", "getdents64", "set_tid_address",
        "restart_syscall", "semtimedop", "fadvise64", "timer_create",
        "timer_settime", "timer_gettime", "timer_getoverrun",
        "timer_delete", "clock_settime", "clock_gettime",
        "clock_getres", "clock_nanosleep", "exit_group",
        "epoll_wait", "epoll_ctl", "tgkill", "utimes", "vserver",
        "mbind", "set_mempolicy", "get_mempolicy", "mq_open",
        "mq_unlink", "mq_timedsend", "mq_timedreceive", "mq_notify",
        "mq_getsetattr", "kexec_load", "waitid", "add_key",
        "request_key", "keyctl", "ioprio_set", "ioprio_get",
        "inotify_init", "inotify_add_watch", "inotify_rm_watch",
        "migrate_pages", "openat", "mkdirat", "mknodat", "fchownat",
        "futimesat", "newfstatat", "unlinkat", "renameat", "linkat",
        "symlinkat", "readlinkat", "fchmodat", "faccessat",
        "pselect6", "ppoll", "unshare", "set_robust_list",
        "get_robust_list", "splice", "tee", "sync_file_range",
        "vmsplice", "move_pages", "utimensat", "epoll_pwait",
        "signalfd", "timerfd_create", "eventfd", "fallocate",
        "timerfd_settime", "timerfd_gettime", "accept4", "signalfd4",
        "eventfd2", "epoll_create1", "dup3", "pipe2", "inotify_init1",
        "preadv", "pwritev", "rt_tgsigqueueinfo", "perf_event_open",
        "recvmmsg", "fanotify_init", "fanotify_mark", "prlimit64",
        "name_to_handle_at", "open_by_handle_at", "clock_adjtime",
        "syncfs", "sendmmsg", "setns", "getcpu", "process_vm_readv",
        "process_vm_writev", "kcmp", "finit_module"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

Create AppArmor profile at `/etc/apparmor.d/docker-mcp`:

```
#include <tunables/global>

profile docker-mcp flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  network,
  capability,
  file,
  umount,

  deny @{PROC}/* w,   # deny write for all files directly in /proc (not in a subdir)
  deny @{PROC}/{[^1-9],[^1-9][^0-9],[^1-9s][^0-9y][^0-9s],[^1-9][^0-9][^0-9][^0-9]*}/** w,
  deny @{PROC}/sys/[^k]** w,  # deny write to all but /proc/sys/kernel/
  deny @{PROC}/sys/kernel/{?,??,[^s][^h][^m]**} w,  # deny write to all but shm* in /proc/sys/kernel/
  deny @{PROC}/sysrq-trigger rwklx,
  deny @{PROC}/mem rwklx,
  deny @{PROC}/kmem rwklx,
  deny @{PROC}/kcore rwklx,

  deny mount,

  deny /sys/[^f]*/** wklx,
  deny /sys/f[^s]*/** wklx,
  deny /sys/fs/[^c]*/** wklx,
  deny /sys/fs/c[^g]*/** wklx,
  deny /sys/fs/cg[^r]*/** wklx,
  deny /sys/firmware/efi/efivars/** rwklx,
  deny /sys/kernel/security/** rwklx,
}
```

Load AppArmor profile:

```bash
sudo apparmor_parser -r /etc/apparmor.d/docker-mcp
```

### 4. SystemD Service

Create `/etc/systemd/system/mcp-optimizer.service`:

```ini
[Unit]
Description=MCP Optimizer Framework
After=network.target redis-server.service docker.service
Requires=redis-server.service

[Service]
Type=simple
User=mcp-optimizer
Group=mcp-optimizer
WorkingDirectory=/opt/mcp-optimizer-framework
Environment="PATH=/opt/mcp-optimizer-framework/venv/bin"
EnvironmentFile=/opt/mcp-optimizer-framework/.env
ExecStart=/opt/mcp-optimizer-framework/venv/bin/python -m mcp_optimizer.cli serve
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/mcp-optimizer /opt/mcp-optimizer-framework/data

# Resource limits
LimitNOFILE=10000
LimitNPROC=100

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mcp-optimizer

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-optimizer
sudo systemctl start mcp-optimizer
sudo systemctl status mcp-optimizer
```

## Deployment Options

### Option 1: Single Server Deployment

Suitable for development and small-scale production.

```bash
# All components on one server
# - Application
# - Redis
# - Prometheus

# Start services
sudo systemctl start redis-server
sudo systemctl start mcp-optimizer
sudo systemctl start prometheus
```

### Option 2: Multi-Server Deployment

Suitable for high availability and scale.

#### Load Balancer (nginx)

Install nginx:

```bash
sudo apt-get install -y nginx
```

Configure `/etc/nginx/sites-available/mcp-optimizer`:

```nginx
upstream mcp_optimizer {
    least_conn;
    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name mcp-optimizer.example.com;

    location / {
        proxy_pass http://mcp_optimizer;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /metrics {
        proxy_pass http://mcp_optimizer/metrics;

        # Restrict access to monitoring systems
        allow 10.0.2.0/24;
        deny all;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/mcp-optimizer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Redis Cluster

Use Redis Sentinel for high availability:

```bash
# On each Redis node, configure sentinel
sudo nano /etc/redis/sentinel.conf
```

```
sentinel monitor mcp-redis 10.0.3.10 6379 2
sentinel down-after-milliseconds mcp-redis 5000
sentinel parallel-syncs mcp-redis 1
sentinel failover-timeout mcp-redis 10000
```

### Option 3: Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-optimizer
  labels:
    app: mcp-optimizer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-optimizer
  template:
    metadata:
      labels:
        app: mcp-optimizer
    spec:
      containers:
      - name: mcp-optimizer
        image: rhart696/mcp-optimizer-framework:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: EXECUTION_MODE
          value: "hybrid"
        - name: SANDBOX_BACKEND
          value: "docker"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: mcp-optimizer-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
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
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-optimizer
spec:
  selector:
    app: mcp-optimizer
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/prometheus.yaml
```

## Monitoring

### Prometheus Configuration

Create `/etc/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'mcp-optimizer'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
```

### Grafana Dashboard

Import dashboard from `dashboards/mcp-optimizer.json` or create custom:

Key metrics to monitor:
- Token usage per request
- Execution time percentiles (p50, p95, p99)
- Cache hit rate
- Error rate
- Active sessions
- Sandbox timeouts
- Resource utilization

### Alerting Rules

Create `/etc/prometheus/rules/mcp-optimizer.yml`:

```yaml
groups:
  - name: mcp_optimizer
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(mcp_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: LowCacheHitRate
        expr: (rate(mcp_cache_hits_total[5m]) / (rate(mcp_cache_hits_total[5m]) + rate(mcp_cache_misses_total[5m]))) < 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}%"

      - alert: HighTokenUsage
        expr: mcp_tokens_used > 5000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High token usage detected"

      - alert: SandboxTimeouts
        expr: rate(mcp_sandbox_timeouts_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Frequent sandbox timeouts"
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow from 10.0.0.0/8 to any port 6379  # Redis (internal only)
sudo ufw allow from 10.0.0.0/8 to any port 9090  # Prometheus (internal only)
sudo ufw enable
```

### 2. SSL/TLS Configuration

Use Let's Encrypt for SSL certificates:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d mcp-optimizer.example.com
```

### 3. Secrets Management

Use environment variables or secrets management systems:

```bash
# Using HashiCorp Vault
vault kv put secret/mcp-optimizer \
  redis_password="secure_password" \
  api_key="secret_key"

# Retrieve in application
export REDIS_PASSWORD=$(vault kv get -field=redis_password secret/mcp-optimizer)
```

### 4. Regular Security Updates

```bash
# Create update script
cat > /opt/mcp-optimizer-framework/update.sh <<'EOF'
#!/bin/bash
cd /opt/mcp-optimizer-framework
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart mcp-optimizer
EOF

chmod +x /opt/mcp-optimizer-framework/update.sh

# Schedule weekly updates
sudo crontab -e
0 2 * * 0 /opt/mcp-optimizer-framework/update.sh
```

## Performance Tuning

### 1. Redis Optimization

```bash
# Increase max clients
echo "maxclients 10000" >> /etc/redis/redis.conf

# Optimize memory
echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf
sysctl -p

# Disable transparent huge pages
echo never > /sys/kernel/mm/transparent_hugepage/enabled
```

### 2. Docker Optimization

```bash
# Increase container limits
cat > /etc/docker/daemon.json <<EOF
{
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  },
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

sudo systemctl restart docker
```

### 3. Application Tuning

Adjust in `.env`:

```bash
# Increase worker processes
WORKERS=4

# Adjust cache TTL based on usage patterns
CACHE_TTL_SECONDS=600

# Tune token limits
MAX_TOKENS_PER_REQUEST=2000
CONTEXT_SIZE_LIMIT_KB=200
```

## Backup and Recovery

### Database Backup

```bash
# Redis backup script
cat > /opt/mcp-optimizer-framework/backup-redis.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
redis-cli --rdb $BACKUP_DIR/dump_$DATE.rdb
find $BACKUP_DIR -mtime +7 -delete
EOF

chmod +x /opt/mcp-optimizer-framework/backup-redis.sh

# Schedule daily backups
sudo crontab -e
0 3 * * * /opt/mcp-optimizer-framework/backup-redis.sh
```

### Application State Backup

```bash
# Backup configuration and data
tar czf /backup/mcp-optimizer-$(date +%Y%m%d).tar.gz \
  /opt/mcp-optimizer-framework/.env \
  /opt/mcp-optimizer-framework/data \
  /var/log/mcp-optimizer
```

## Health Checks

Create health check endpoints:

```python
# In your application
@app.route('/health')
async def health():
    return {'status': 'healthy', 'version': '1.0.0'}

@app.route('/ready')
async def ready():
    # Check dependencies
    redis_ok = await check_redis()
    docker_ok = await check_docker()
    return {
        'ready': redis_ok and docker_ok,
        'checks': {
            'redis': redis_ok,
            'docker': docker_ok
        }
    }
```

## Logging

Configure structured logging:

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
```

Ship logs to centralized logging:

```bash
# Install filebeat
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.11.0-amd64.deb
sudo dpkg -i filebeat-8.11.0-amd64.deb

# Configure filebeat
sudo nano /etc/filebeat/filebeat.yml
```

## Disaster Recovery

### Recovery Time Objective (RTO): 15 minutes
### Recovery Point Objective (RPO): 5 minutes

1. **Restore Redis from backup**
2. **Deploy new application instances**
3. **Restore configuration**
4. **Verify health checks**
5. **Resume traffic**

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## Next Steps

- Configure monitoring alerts
- Set up log aggregation
- Perform load testing
- Create runbooks for common operations
- Schedule regular security audits

## Support

For deployment assistance:
- GitHub Issues: https://github.com/rhart696/mcp-optimizer-framework/issues
- Documentation: https://github.com/rhart696/mcp-optimizer-framework/docs

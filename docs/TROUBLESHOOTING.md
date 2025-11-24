# Troubleshooting Guide

Common issues and solutions for MCP Optimizer Framework v1.0.0.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Sandbox Issues](#sandbox-issues)
- [Redis Connection Issues](#redis-connection-issues)
- [Performance Issues](#performance-issues)
- [Memory Issues](#memory-issues)
- [Docker Issues](#docker-issues)
- [Metrics and Monitoring](#metrics-and-monitoring)
- [Token Limit Issues](#token-limit-issues)
- [Error Messages](#error-messages)
- [Debugging Tips](#debugging-tips)

## Installation Issues

### Issue: `ImportError: No module named 'mcp_optimizer'`

**Symptom:** Cannot import mcp_optimizer modules after installation.

**Solution:**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall package
pip install -e .

# Verify installation
python -c "import mcp_optimizer; print(mcp_optimizer.__version__)"
```

### Issue: Dependency conflicts during installation

**Symptom:** pip fails to resolve dependencies.

**Solution:**
```bash
# Create fresh virtual environment
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies in order
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e .
```

### Issue: `ModuleNotFoundError: No module named 'structlog'`

**Symptom:** Missing required dependencies.

**Solution:**
```bash
# Install missing dependencies
pip install structlog pydantic aiohttp

# Or reinstall all requirements
pip install -r requirements.txt
```

## Sandbox Issues

### Issue: Docker sandbox not available

**Symptom:** `RuntimeError: Docker not available` or sandbox falls back to basic mode.

**Diagnosis:**
```bash
# Check if Docker is running
docker ps

# Check if user has Docker permissions
docker run hello-world

# Check Docker socket permissions
ls -l /var/run/docker.sock
```

**Solution:**
```bash
# Start Docker if not running
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo (not recommended for production)
# Set in .env:
SANDBOX_BACKEND=basic
```

### Issue: Sandbox timeout errors

**Symptom:** `TimeoutError: Execution exceeded 30s limit`

**Diagnosis:**
```bash
# Check sandbox backend
mcp-optimizer capabilities | grep sandbox

# Monitor container execution
docker ps -a | grep mcp
```

**Solution:**
```bash
# Increase timeout in .env
MAX_EXECUTION_TIME=60

# Or programmatically
result = await sandbox.execute(code, timeout=60)

# Check for infinite loops in generated code
# Enable debug logging to see generated code
LOG_LEVEL=DEBUG
```

### Issue: Seccomp profile not found

**Symptom:** `docker: Error response from daemon: path /etc/docker/seccomp-mcp.json not found`

**Solution:**
```bash
# Create seccomp profile
sudo cp docs/examples/seccomp-mcp.json /etc/docker/seccomp-mcp.json

# Or disable seccomp (less secure)
# Remove from sandbox.py:
# "--security-opt", "seccomp=/etc/docker/seccomp-mcp.json",
```

### Issue: AppArmor profile errors

**Symptom:** `Error response from daemon: AppArmor enabled on system but profile not found`

**Solution:**
```bash
# Check AppArmor status
sudo aa-status | grep docker-mcp

# Load profile
sudo apparmor_parser -r /etc/apparmor.d/docker-mcp

# Or disable AppArmor for testing
# Remove from sandbox.py:
# "--security-opt", "apparmor=docker-mcp",
```

## Redis Connection Issues

### Issue: Cannot connect to Redis

**Symptom:** `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Diagnosis:**
```bash
# Check if Redis is running
systemctl status redis-server

# Test connection
redis-cli ping

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

**Solution:**
```bash
# Start Redis
sudo systemctl start redis-server

# Check Redis is listening
netstat -tlnp | grep 6379

# Update REDIS_URL in .env if using different host/port
REDIS_URL=redis://localhost:6379/0

# Check firewall
sudo ufw allow from 127.0.0.1 to any port 6379
```

### Issue: Redis authentication failed

**Symptom:** `redis.exceptions.AuthenticationError: Authentication required`

**Solution:**
```bash
# Set password in .env
REDIS_PASSWORD=your_password_here

# Update REDIS_URL with password
REDIS_URL=redis://:your_password_here@localhost:6379/0

# Or disable authentication in /etc/redis/redis.conf
# Comment out: requirepass
sudo systemctl restart redis-server
```

### Issue: Redis out of memory

**Symptom:** `redis.exceptions.ResponseError: OOM command not allowed`

**Diagnosis:**
```bash
# Check Redis memory usage
redis-cli info memory

# Check maxmemory setting
redis-cli config get maxmemory
```

**Solution:**
```bash
# Increase Redis memory in /etc/redis/redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server

# Or flush old data
redis-cli FLUSHDB
```

## Performance Issues

### Issue: Slow execution times

**Symptom:** Operations take longer than expected (>500ms).

**Diagnosis:**
```bash
# Check metrics
mcp-optimizer metrics

# Check system resources
top
htop
docker stats

# Enable profiling
LOG_LEVEL=DEBUG
```

**Solution:**
```bash
# Enable caching
ENABLE_CACHING=true
CACHE_TTL_SECONDS=600

# Use hybrid mode for simple queries
EXECUTION_MODE=hybrid

# Increase Redis memory
# Tune Docker resources in daemon.json

# Check for network latency to Redis
redis-cli --latency

# Consider using memory backend for testing
# In code:
context = ContextManager(backend="memory")
```

### Issue: High CPU usage

**Symptom:** CPU at 90%+ constantly.

**Diagnosis:**
```bash
# Check which process is using CPU
top -c
ps aux | grep python

# Check Docker container stats
docker stats

# Profile the application
python -m cProfile -o profile.stats mcp_optimizer/cli.py
```

**Solution:**
```bash
# Limit Docker CPU
# In docker run command add:
--cpus="1.0"

# Reduce worker count
WORKERS=2

# Check for infinite loops in generated code
# Add execution limits
# Set CPU resource limits in sandbox
```

### Issue: High token usage

**Symptom:** Excessive token consumption, high costs.

**Diagnosis:**
```bash
# Check token metrics
mcp-optimizer metrics | grep tokens

# Enable token tracking
ENABLE_METRICS=true

# Check Prometheus metrics
curl http://localhost:9090/metrics | grep mcp_tokens
```

**Solution:**
```bash
# Reduce token limits
MAX_TOKENS_PER_REQUEST=500

# Enable aggressive caching
CACHE_TTL_SECONDS=900

# Use hybrid mode to leverage MCP for simple queries
EXECUTION_MODE=hybrid

# Reduce context size
CONTEXT_SIZE_LIMIT_KB=50

# Review generated code efficiency
LOG_LEVEL=DEBUG
```

## Memory Issues

### Issue: Out of memory errors

**Symptom:** `MemoryError` or process killed by OOM killer.

**Diagnosis:**
```bash
# Check system memory
free -h

# Check process memory
ps aux --sort=-%mem | head

# Check Docker container memory
docker stats

# Check kernel logs for OOM
dmesg | grep -i "out of memory"
```

**Solution:**
```bash
# Increase system memory or swap

# Reduce memory limits
MAX_MEMORY_MB=256

# Limit context size
CONTEXT_SIZE_LIMIT_KB=50

# Enable Redis memory eviction
# In /etc/redis/redis.conf:
maxmemory-policy allkeys-lru

# Restart application periodically
# Add to systemd service:
RuntimeMaxSec=86400
```

### Issue: Memory leaks

**Symptom:** Memory usage grows over time.

**Diagnosis:**
```bash
# Monitor memory growth
watch -n 5 'ps aux | grep mcp-optimizer'

# Use memory profiler
pip install memory_profiler
python -m memory_profiler mcp_optimizer/cli.py
```

**Solution:**
```bash
# Restart service daily
sudo systemctl restart mcp-optimizer

# Check for unclosed connections
# Add cleanup in __del__ methods
# Use context managers for resources

# Profile and fix leaks
# Common causes:
# - Unclosed Redis connections
# - Docker containers not cleaned up
# - Large context not being cleared
```

## Docker Issues

### Issue: Docker daemon not running

**Symptom:** `Cannot connect to the Docker daemon`

**Solution:**
```bash
# Start Docker
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

### Issue: Permission denied for Docker socket

**Symptom:** `Got permission denied while trying to connect to the Docker daemon socket`

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group membership
newgrp docker

# Or change socket permissions (less secure)
sudo chmod 666 /var/run/docker.sock
```

### Issue: Too many Docker containers

**Symptom:** `no space left on device` or slow Docker operations.

**Diagnosis:**
```bash
# Check containers
docker ps -a | wc -l

# Check disk usage
docker system df
```

**Solution:**
```bash
# Remove stopped containers
docker container prune -f

# Remove old images
docker image prune -a -f

# Clean up everything
docker system prune -a -f --volumes

# Set up automatic cleanup
# Add to cron:
0 2 * * * docker system prune -f
```

### Issue: Docker pull rate limit

**Symptom:** `You have reached your pull rate limit`

**Solution:**
```bash
# Login to Docker Hub
docker login

# Or use alternative registry
# Change in sandbox.py:
"your-registry.com/python:3.11-slim"

# Or build custom image
docker build -t mcp-python:latest .
```

## Metrics and Monitoring

### Issue: Prometheus metrics not appearing

**Symptom:** `/metrics` endpoint returns empty or error.

**Diagnosis:**
```bash
# Check if metrics enabled
grep ENABLE_METRICS .env

# Test metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus logs
tail -f /var/log/prometheus/prometheus.log
```

**Solution:**
```bash
# Enable metrics
ENABLE_METRICS=true

# Restart application
sudo systemctl restart mcp-optimizer

# Check Prometheus scrape config
cat /etc/prometheus/prometheus.yml

# Verify network connectivity
telnet localhost 9090
```

### Issue: Missing metrics in Grafana

**Symptom:** Grafana dashboard shows "No data".

**Solution:**
```bash
# Check Prometheus data source in Grafana
# Settings -> Data Sources -> Prometheus

# Test query in Prometheus
# http://localhost:9090/graph
# Query: mcp_tokens_used

# Check time range in Grafana

# Force metrics generation
# Execute some operations to generate metrics
mcp-optimizer benchmark
```

## Token Limit Issues

### Issue: Token limit exceeded frequently

**Symptom:** `429 error: Token limit exceeded`

**Diagnosis:**
```bash
# Check current limits
grep MAX_TOKENS .env

# Check actual usage
mcp-optimizer metrics | grep tokens
```

**Solution:**
```bash
# Increase limit
MAX_TOKENS_PER_REQUEST=2000

# Optimize code generation
# Reduce context size
CONTEXT_SIZE_LIMIT_KB=50

# Use caching more aggressively
CACHE_TTL_SECONDS=900

# Switch to hybrid mode
EXECUTION_MODE=hybrid
```

## Error Messages

### `structlog.exceptions.DropEvent: Log event was dropped by processor`

**Cause:** Log filtering configuration issue.

**Solution:**
```python
# Adjust log level
LOG_LEVEL=INFO

# Or configure structlog properly
import structlog
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)
```

### `asyncio.TimeoutError`

**Cause:** Operation took too long.

**Solution:**
```bash
# Increase timeout
MAX_EXECUTION_TIME=60

# Check for blocking operations
# Use async/await properly
# Avoid synchronous I/O in async context
```

### `RuntimeError: Sandbox execution failed`

**Cause:** Sandbox backend error.

**Solution:**
```bash
# Check sandbox backend
mcp-optimizer capabilities

# Switch to different backend
SANDBOX_BACKEND=basic

# Check Docker/seccomp/AppArmor configuration
# See sandbox issues above
```

### `ValueError: Invalid execution mode`

**Cause:** Invalid configuration.

**Solution:**
```bash
# Valid modes: mcp_only, code_execution, hybrid
EXECUTION_MODE=hybrid

# Check for typos in .env
```

## Debugging Tips

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG
LOG_FORMAT=json

# Restart service
sudo systemctl restart mcp-optimizer

# View logs
sudo journalctl -u mcp-optimizer -f
```

### Inspect Generated Code

```python
from mcp_optimizer import CodeExecutor, FeatureFlags

flags = FeatureFlags()
executor = CodeExecutor(flags)

# Print generated code
code = executor.generate_code("list_errors", {})
print(code)
```

### Test Sandbox Manually

```python
from mcp_optimizer import SecureSandbox
import asyncio

async def test():
    sandbox = SecureSandbox(backend="docker")
    result = await sandbox.execute("print('Hello from sandbox')")
    print(result)

asyncio.run(test())
```

### Check Redis Connection

```bash
# Test Redis
redis-cli
127.0.0.1:6379> PING
PONG

# List keys
127.0.0.1:6379> KEYS *

# Monitor commands
redis-cli MONITOR
```

### Profile Performance

```bash
# Install profiling tools
pip install py-spy

# Profile running process
py-spy top --pid $(pgrep -f mcp-optimizer)

# Generate flamegraph
py-spy record -o profile.svg --pid $(pgrep -f mcp-optimizer)
```

### Test Docker Sandbox

```bash
# Test Docker manually
docker run --rm \
  --network none \
  --memory 512m \
  --cpus 0.5 \
  --read-only \
  python:3.11-slim \
  python -c "print('Docker sandbox test')"
```

### Verify Metrics Collection

```python
from mcp_optimizer import MetricsCollector

metrics = MetricsCollector(enabled=True)

with metrics.measure("test", {"operation": "test"}):
    import time
    time.sleep(0.1)

print(metrics.get_summary())
```

## Getting Help

If you've tried these solutions and still have issues:

1. **Check existing issues**: https://github.com/rhart696/mcp-optimizer-framework/issues
2. **Create new issue**: Include:
   - Framework version (`mcp-optimizer --version`)
   - Python version (`python --version`)
   - OS and version (`uname -a`)
   - Full error message and traceback
   - Configuration (sanitized `.env`)
   - Relevant logs
3. **Enable debug mode** and include debug output
4. **Provide minimal reproduction** if possible

## Common Patterns

### Issue Investigation Template

```bash
# 1. Check service status
sudo systemctl status mcp-optimizer

# 2. Check logs
sudo journalctl -u mcp-optimizer -n 100 --no-pager

# 3. Check dependencies
systemctl status redis-server
systemctl status docker

# 4. Check resources
df -h
free -h
docker stats

# 5. Check metrics
curl http://localhost:9090/metrics

# 6. Test connectivity
redis-cli PING
docker ps
```

### Quick Recovery

```bash
# Nuclear option - restart everything
sudo systemctl restart redis-server
sudo systemctl restart docker
docker system prune -f
sudo systemctl restart mcp-optimizer

# Check status
sudo systemctl status mcp-optimizer
```

## Preventive Measures

1. **Monitor metrics proactively**
2. **Set up alerting** (see DEPLOYMENT.md)
3. **Regular backups** of Redis data
4. **Keep dependencies updated**
5. **Review logs regularly**
6. **Load test before production**
7. **Document custom configurations**

## Additional Resources

- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Performance Guide](PERFORMANCE.md)
- [GitHub Issues](https://github.com/rhart696/mcp-optimizer-framework/issues)

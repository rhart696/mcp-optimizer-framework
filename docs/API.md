# API Reference

Complete API reference for MCP Optimizer Framework v1.0.0.

## Table of Contents

- [Core Module](#core-module)
- [Sandbox Module](#sandbox-module)
- [Context Module](#context-module)
- [Metrics Module](#metrics-module)
- [Sessions Module](#sessions-module)
- [Capabilities Module](#capabilities-module)
- [Telemetry Module](#telemetry-module)
- [CLI Module](#cli-module)

## Core Module

### `CodeExecutor`

Main execution orchestrator for MCP operations.

```python
from mcp_optimizer import CodeExecutor, FeatureFlags

executor = CodeExecutor(flags: FeatureFlags)
```

#### Constructor Parameters

- `flags` (FeatureFlags): Configuration flags for the executor

#### Methods

##### `async execute_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]`

Execute an operation with full production hardening.

**Parameters:**
- `intent` (str): The operation to execute (e.g., "list_errors", "analyze_error")
- `params` (Dict[str, Any]): Parameters for the operation

**Returns:**
- `Dict[str, Any]`: Structured JSON response with metadata

**Raises:**
- `TimeoutError`: If execution exceeds time limit
- `RuntimeError`: If sandbox execution fails

**Example:**
```python
result = await executor.execute_intent(
    intent="list_errors",
    params={"filter": "active", "limit": 10}
)
```

##### `structured_response(data: Any) -> Dict[str, Any]`

Create a structured JSON Schema response.

**Parameters:**
- `data` (Any): Response data to wrap

**Returns:**
- `Dict[str, Any]`: Structured response with metadata

**Response Schema:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "data": {...},
    "metadata": {
      "tokens_used": 125,
      "execution_time_ms": 45.2,
      "cache_hit": false,
      "mode": "code_execution"
    }
  },
  "schema": "https://mcp-optimizer.dev/schemas/response/v2"
}
```

##### `error_response(message: str, code: int) -> Dict[str, Any]`

Create a structured error response.

**Parameters:**
- `message` (str): Error message
- `code` (int): HTTP-style error code

**Returns:**
- `Dict[str, Any]`: Structured error response

##### `estimate_tokens(intent: str, params: Dict[str, Any]) -> int`

Estimate token usage for rate limiting.

**Parameters:**
- `intent` (str): Operation intent
- `params` (Dict[str, Any]): Operation parameters

**Returns:**
- `int`: Estimated token count

### `FeatureFlags`

Configuration flags for gradual migration and feature control.

```python
from mcp_optimizer import FeatureFlags, ExecutionMode

flags = FeatureFlags(
    execution_mode=ExecutionMode.HYBRID,
    enable_sandbox=True,
    enable_caching=True,
    enable_metrics=True,
    enable_auto_apply=False,
    max_tokens_per_request=1000,
    cache_ttl_seconds=300,
    context_size_limit_kb=100
)
```

#### Fields

- `execution_mode` (ExecutionMode): Execution strategy (MCP_ONLY, CODE_EXECUTION, HYBRID)
- `enable_sandbox` (bool): Enable security sandboxing (default: True)
- `enable_caching` (bool): Enable context caching (default: True)
- `enable_metrics` (bool): Enable metrics collection (default: True)
- `enable_auto_apply` (bool): Enable automatic fix application (default: False)
- `max_tokens_per_request` (int): Maximum tokens per request (default: 1000)
- `cache_ttl_seconds` (int): Cache TTL in seconds (default: 300)
- `context_size_limit_kb` (int): Context size limit in KB (default: 100)

### `ExecutionMode`

Enum for execution modes.

```python
from mcp_optimizer import ExecutionMode

# Available modes
ExecutionMode.MCP_ONLY        # Traditional MCP approach
ExecutionMode.CODE_EXECUTION  # Optimized code execution
ExecutionMode.HYBRID          # Smart routing between both
```

### `IntentRouter`

Routes requests to appropriate handler based on intent and execution mode.

```python
from mcp_optimizer.core import IntentRouter, FeatureFlags

router = IntentRouter(flags: FeatureFlags)
```

#### Methods

##### `async route(intent: str, params: Dict[str, Any]) -> Dict[str, Any]`

Route request based on intent and execution mode.

**Parameters:**
- `intent` (str): Operation intent
- `params` (Dict[str, Any]): Operation parameters

**Returns:**
- `Dict[str, Any]`: Execution result

## Sandbox Module

### `SecureSandbox`

Production-grade sandbox with multiple backend support.

```python
from mcp_optimizer import SecureSandbox

sandbox = SecureSandbox(
    enabled=True,
    backend="docker"  # docker, firecracker, wasi, seccomp, basic
)
```

#### Constructor Parameters

- `enabled` (bool): Enable sandbox (default: True)
- `backend` (str): Sandbox backend to use (default: "docker")

#### Security Limits

Default security limits applied:
- CPU: 30 seconds
- Memory: 512 MB
- Disk: 100 MB
- Processes: 50
- File handles: 100
- Network: Disabled
- Filesystem: Read-only

#### Methods

##### `async execute(code: str, timeout: int = 30, memory_mb: int = 512) -> Dict[str, Any]`

Execute code with full security enforcement.

**Parameters:**
- `code` (str): Python code to execute
- `timeout` (int): Execution timeout in seconds (default: 30)
- `memory_mb` (int): Memory limit in MB (default: 512)

**Returns:**
- `Dict[str, Any]`: Execution result with stdout, stderr, and exit_code

**Raises:**
- `TimeoutError`: If execution exceeds timeout
- `RuntimeError`: If sandbox execution fails

**Example:**
```python
result = await sandbox.execute(
    code='''
import requests
result = requests.get('https://api.example.com').json()
print(result)
''',
    timeout=30,
    memory_mb=256
)

print(result['stdout'])
print(result['exit_code'])
```

##### `cleanup()`

Clean up sandbox resources and workspace.

**Example:**
```python
sandbox.cleanup()
```

### `HardenedSandbox`

Extended sandbox with gVisor and additional isolation layers.

```python
from mcp_optimizer import HardenedSandbox

sandbox = HardenedSandbox(
    use_gvisor=True,
    network_policies=["deny_all"],
    filesystem_policies=["read_only"]
)
```

## Context Module

### `ContextManager`

Manages contextual information and cross-session state.

```python
from mcp_optimizer import ContextManager

context = ContextManager(
    backend="redis",      # redis or memory
    ttl=300,             # TTL in seconds
    size_limit_kb=100    # Size limit in KB
)
```

#### Constructor Parameters

- `backend` (str): Storage backend ("redis" or "memory")
- `ttl` (int): Time-to-live in seconds
- `size_limit_kb` (int): Maximum context size in KB

#### Methods

##### `async set(key: str, value: Any, ttl: Optional[int] = None) -> None`

Set a context value.

**Parameters:**
- `key` (str): Context key
- `value` (Any): Value to store (must be JSON-serializable)
- `ttl` (Optional[int]): Custom TTL for this key (optional)

**Example:**
```python
await context.set("current_error", {"id": "123", "type": "ValueError"})
await context.set("temp_data", {...}, ttl=60)  # 60-second TTL
```

##### `async get(key: str) -> Optional[Any]`

Get a context value.

**Parameters:**
- `key` (str): Context key

**Returns:**
- `Optional[Any]`: Stored value or None if not found

**Example:**
```python
error = await context.get("current_error")
if error:
    print(f"Current error: {error['id']}")
```

##### `async delete(key: str) -> None`

Delete a context value.

##### `async clear() -> None`

Clear all context values.

##### `async size() -> int`

Get current context size in bytes.

##### `property last_cache_hit: bool`

Whether the last operation was a cache hit.

## Metrics Module

### `MetricsCollector`

Production metrics collection with Prometheus integration.

```python
from mcp_optimizer import MetricsCollector

metrics = MetricsCollector(enabled=True)
```

#### Constructor Parameters

- `enabled` (bool): Enable metrics collection (default: True)

#### Methods

##### `measure(metric_name: str, labels: Optional[Dict[str, str]] = None)`

Context manager for measuring execution time.

**Parameters:**
- `metric_name` (str): Metric name
- `labels` (Optional[Dict[str, str]]): Metric labels

**Example:**
```python
with metrics.measure("execution_time", {"intent": "list_errors"}):
    result = await execute_operation()
```

##### `increment(metric_name: str, labels: Optional[Dict[str, str]] = None)`

Increment a counter metric.

**Supported Metrics:**
- `execution_success`
- `cache_hit`
- `cache_miss`
- `token_limit_exceeded`
- `sandbox_rejection`
- `sandbox_timeout`

**Example:**
```python
metrics.increment("cache_hit", {"type": "session"})
metrics.increment("token_limit_exceeded")
```

##### `observe(metric_name: str, value: float, labels: Optional[Dict[str, str]] = None)`

Record a histogram observation.

**Supported Metrics:**
- `tokens_used`
- `context_size`

**Example:**
```python
metrics.observe("tokens_used", 125, {"intent": "analyze", "mode": "code_execution"})
```

##### `set_gauge(metric_name: str, value: float, labels: Optional[Dict[str, str]] = None)`

Set a gauge value.

**Supported Metrics:**
- `active_sessions`

**Example:**
```python
metrics.set_gauge("active_sessions", 42)
```

##### `get_last(metric_name: str) -> Optional[float]`

Get last recorded value for a metric.

##### `export_metrics() -> bytes`

Export metrics in Prometheus format.

**Example:**
```python
prometheus_data = metrics.export_metrics()
```

##### `get_summary() -> Dict[str, Any]`

Get current metrics summary.

**Returns:**
```python
{
    "cache_hit_rate": "85.3%",
    "total_errors": 12,
    "last_tokens_used": 125,
    "estimated_session_cost": "$0.0013",
    "active_sessions": 5
}
```

##### `alert_if_threshold()`

Check thresholds and alert if exceeded.

## Sessions Module

### `SessionManager`

Manages session lifecycle and state persistence.

```python
from mcp_optimizer import SessionManager

sessions = SessionManager(
    redis_url="redis://localhost:6379",
    default_ttl=3600
)
```

#### Constructor Parameters

- `redis_url` (str): Redis connection URL
- `default_ttl` (int): Default session TTL in seconds

#### Methods

##### `async create_session(session_id: str, data: Dict[str, Any]) -> None`

Create a new session.

**Parameters:**
- `session_id` (str): Unique session identifier
- `data` (Dict[str, Any]): Initial session data

##### `async get_session(session_id: str) -> Optional[Dict[str, Any]]`

Get session data.

##### `async update_session(session_id: str, data: Dict[str, Any]) -> None`

Update session data.

##### `async delete_session(session_id: str) -> None`

Delete a session.

##### `async list_sessions() -> List[str]`

List all active session IDs.

##### `async cleanup_expired() -> int`

Clean up expired sessions. Returns count of cleaned sessions.

## Capabilities Module

### `CapabilityDetector`

Automatic detection of available MCP capabilities.

```python
from mcp_optimizer import CapabilityDetector

detector = CapabilityDetector()
```

#### Methods

##### `async detect() -> Dict[str, List[str]]`

Detect available capabilities.

**Returns:**
```python
{
    "sandbox": ["docker", "seccomp"],
    "storage": ["redis", "memory"],
    "metrics": ["prometheus"],
    "integrations": ["sentry", "github"]
}
```

##### `async check_capability(name: str) -> bool`

Check if a specific capability is available.

**Example:**
```python
has_docker = await detector.check_capability("docker")
if has_docker:
    use_docker_sandbox()
```

##### `async get_feature_flags() -> FeatureFlags`

Get recommended feature flags based on detected capabilities.

## Telemetry Module

### `TelemetryCollector`

Comprehensive telemetry and audit logging.

```python
from mcp_optimizer import TelemetryCollector

telemetry = TelemetryCollector(
    enable_audit=True,
    enable_tracing=True,
    export_endpoint="https://telemetry.example.com"
)
```

#### Constructor Parameters

- `enable_audit` (bool): Enable audit logging
- `enable_tracing` (bool): Enable distributed tracing
- `export_endpoint` (str): Telemetry export endpoint

#### Methods

##### `async log_event(event: str, data: Dict[str, Any]) -> None`

Log an audit event.

**Example:**
```python
await telemetry.log_event("code_execution", {
    "intent": "fix_error",
    "user": "user123",
    "timestamp": datetime.now().isoformat()
})
```

##### `async start_trace(operation: str) -> str`

Start a distributed trace. Returns trace_id.

##### `async end_trace(trace_id: str) -> None`

End a distributed trace.

##### `async export() -> None`

Export telemetry data to configured endpoint.

## CLI Module

### Command Line Interface

The CLI provides management and operational commands.

#### Commands

##### `mcp-optimizer init`

Initialize configuration.

```bash
mcp-optimizer init --mode hybrid --enable-metrics --sandbox docker
```

**Options:**
- `--mode`: Execution mode (mcp_only, code_execution, hybrid)
- `--enable-metrics`: Enable metrics collection
- `--sandbox`: Sandbox backend (docker, seccomp, basic)

##### `mcp-optimizer benchmark`

Run performance benchmarks.

```bash
mcp-optimizer benchmark --iterations 1000 --output results.json
```

**Options:**
- `--iterations`: Number of benchmark iterations
- `--output`: Output file for results

##### `mcp-optimizer capabilities`

Check available capabilities.

```bash
mcp-optimizer capabilities --format json
```

##### `mcp-optimizer metrics`

View current metrics.

```bash
mcp-optimizer metrics --export --format prometheus
```

##### `mcp-optimizer sessions`

Manage sessions.

```bash
mcp-optimizer sessions list
mcp-optimizer sessions cleanup
mcp-optimizer sessions delete <session-id>
```

## Error Handling

All async methods may raise:
- `TimeoutError`: Operation timeout
- `RuntimeError`: Execution failure
- `ValueError`: Invalid parameters
- `ConnectionError`: Backend connection failure

## Thread Safety

All components are designed for async/await and are thread-safe when used with asyncio. Do not use threading module directly.

## Type Hints

The framework uses Pydantic for validation and provides full type hints. Use mypy for static type checking:

```bash
mypy mcp_optimizer/
```

## Performance Considerations

- **Token Reduction**: 99.6% reduction vs traditional MCP
- **Latency**: ~50ms average execution time
- **Throughput**: 1000+ operations per second
- **Memory**: <100MB per session

## Security Notes

- Always enable sandbox in production
- Use Docker or Firecracker backend for maximum isolation
- Enable audit logging for compliance
- Set appropriate resource limits
- Review generated code before enabling `enable_auto_apply`

## Version Compatibility

- Python: 3.8+
- Redis: 4.0+
- Docker: 20.10+ (if using Docker sandbox)
- Prometheus: 2.0+ (for metrics export)

## Next Steps

- See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- See [examples/](../examples/) for usage examples

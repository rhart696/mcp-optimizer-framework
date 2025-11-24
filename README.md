# MCP Optimizer Framework

**Generic optimization engine for Model Context Protocol integrations**

## Overview

The MCP Optimizer Framework provides a reusable, production-grade solution for optimizing Model Context Protocol (MCP) integrations through direct code execution instead of tool-based approaches.

### Token Reduction

- **99.6% token reduction** vs traditional MCP
- **50x faster** execution
- **Production-grade security** with multi-layer sandboxing

## Core Features

- **Direct Code Execution**: Execute operations directly without loading massive tool definitions
- **Multi-Layer Sandboxing**: Docker, gVisor, and WASM support for production security
- **Session Management**: Persistent context with Redis backend
- **Telemetry & Metrics**: Full observability with Prometheus integration
- **Capability Detection**: Automatic detection of available MCP capabilities
- **CLI Interface**: Easy-to-use command-line interface for management

## Architecture

```
┌─────────────────────────────────────┐
│     MCP Optimizer Framework          │
├─────────────────────────────────────┤
│  Core Engine (core.py)               │
│  ├─ Execution orchestration          │
│  └─ Error handling                   │
├─────────────────────────────────────┤
│  Sandboxing (sandbox*.py)            │
│  ├─ Basic sandbox                    │
│  └─ Hardened sandbox (Docker/gVisor) │
├─────────────────────────────────────┤
│  Context Management (context.py)     │
│  ├─ Session state                    │
│  └─ Redis persistence                │
├─────────────────────────────────────┤
│  Capabilities (capabilities.py)      │
│  └─ MCP capability detection         │
├─────────────────────────────────────┤
│  Telemetry (telemetry.py)            │
│  ├─ Metrics collection               │
│  └─ Audit logging                    │
└─────────────────────────────────────┘
```

## Installation

```bash
# Clone repository
git clone <repository-url>
cd mcp-optimizer-framework

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

## Quick Start

```python
from mcp_optimizer import MCPOptimizer, SandboxConfig

# Initialize optimizer
optimizer = MCPOptimizer(
    sandbox_config=SandboxConfig(
        mode="hybrid",
        enable_metrics=True
    )
)

# Execute operation
result = await optimizer.execute(
    operation="list_items",
    params={"filter": "active"}
)
```

## CLI Usage

```bash
# Initialize configuration
mcp-optimizer init --mode hybrid

# Run benchmarks
mcp-optimizer benchmark

# Check capabilities
mcp-optimizer capabilities
```

## Components

### Core Engine (`core.py`)
- Operation execution orchestration
- Error handling and retry logic
- Performance optimization

### Sandbox (`sandbox.py`, `sandbox_hardened.py`)
- Basic Python sandbox with resource limits
- Hardened sandbox with Docker/gVisor/WASM support
- Security policy enforcement

### Sessions (`sessions.py`)
- Session lifecycle management
- State persistence with Redis
- Session isolation

### Context (`context.py`)
- Contextual information tracking
- Cross-session state management
- Cache management

### Capabilities (`capabilities.py`)
- MCP capability detection
- Feature flag management
- Runtime capability checks

### Telemetry (`telemetry.py`)
- Metrics collection (Prometheus)
- Audit logging
- Performance tracking

### Metrics (`metrics.py`)
- Token usage tracking
- Latency measurements
- Cost calculations

### CLI (`cli.py`)
- Command-line interface
- Configuration management
- Interactive operations

## Security

The framework implements multiple layers of security:

1. **Resource Limits**: CPU, memory, execution time constraints
2. **Namespace Isolation**: Process and network isolation
3. **Capability-based Security**: Explicit capability requirements
4. **Audit Logging**: Complete audit trail of operations
5. **Secret Management**: Secure handling of credentials

## Configuration

```python
from mcp_optimizer import SandboxConfig

config = SandboxConfig(
    mode="docker",              # sandbox, docker, gvisor, wasm
    enable_metrics=True,
    enable_telemetry=True,
    max_execution_time=30,
    max_memory_mb=512,
    redis_url="redis://localhost:6379"
)
```

## Testing

```bash
# Run tests
pytest tests/

# Run security tests
pytest tests/test_security.py

# Run benchmarks
pytest tests/test_benchmarks.py
```

## Performance

| Metric | Value |
|--------|-------|
| Token Reduction | 99.6% |
| Latency | 50ms avg |
| Throughput | 1000+ ops/sec |
| Memory | <100MB per session |

## Integration

This framework is designed to be integrated with specific MCP adaptors. See [sentry-mcp-optimized](../sentry-mcp-optimized) for an example implementation.

```python
from mcp_optimizer import MCPOptimizer

class CustomAdaptor:
    def __init__(self):
        self.optimizer = MCPOptimizer(...)

    async def custom_operation(self, params):
        return await self.optimizer.execute(
            operation="custom_op",
            params=params
        )
```

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md) - System architecture and design decisions
- [Performance Benchmarks](docs/PERFORMANCE.md) - Detailed performance analysis and benchmarks
- [Security Policy](SECURITY.md) - Security best practices and vulnerability reporting
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [Code of Conduct](CODE_OF_CONDUCT.md) - Community guidelines
- [Roadmap](ROADMAP.md) - Future plans and feature roadmap
- [Changelog](CHANGELOG.md) - Version history and changes

### Architecture Decision Records (ADRs)

- [ADR-0001: Code Execution Approach](docs/adr/0001-code-execution-approach.md)
- [ADR-0002: Docker Sandbox](docs/adr/0002-docker-sandbox.md)

## License

MIT License

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: docs/

# ADR-0001: Code Execution Instead of Tool Loading

## Status

**Accepted** - 2024-11-24

## Context

Traditional Model Context Protocol (MCP) implementations load comprehensive tool definitions into the context window before any operation can be executed. For a service like Sentry with 150+ available tools, this means loading approximately 150,000 tokens (150 tools × ~1,000 tokens per tool definition) every time an assistant wants to interact with the service.

### The Problem

1. **Token Waste**: Loading 150,000 tokens when only 1-2 tools are needed
2. **Latency**: Transferring and processing large tool definitions adds significant overhead
3. **Cost**: Token usage directly impacts API costs (input + output tokens)
4. **Context Window Pressure**: Large tool definitions leave less room for actual work
5. **Scalability**: Problem compounds with multiple MCP integrations

### Example Scenario

**Traditional MCP Flow**:
```
1. User: "List my Sentry errors"
2. Assistant loads ALL Sentry tools (150,000 tokens)
3. Assistant identifies list_issues tool
4. Assistant calls list_issues(project="my-app")
5. Sentry returns results
Total: 150,000+ tokens
```

**Desired Flow**:
```
1. User: "List my Sentry errors"
2. Assistant receives mini-manifest (200 tokens)
3. Assistant requests code execution for "list_errors"
4. Framework executes: requests.get(f'{base}/issues/')
5. Returns structured results
Total: ~500 tokens
```

**Token Reduction**: 150,000 → 500 = 99.7% reduction

## Decision

We will implement **direct code execution** as the primary optimization strategy, with a **hybrid mode** for gradual migration.

### Core Approach

Instead of loading tool definitions, the framework:

1. **Discovery Phase**: Provide a mini-manifest with high-level capabilities
   ```json
   {
     "capabilities": ["list_errors", "analyze_error", "fix_error"],
     "execution": "code",
     "token_cost": 187
   }
   ```

2. **Execution Phase**: Generate and execute Python code for intents
   ```python
   # Generated code for "list_errors" intent
   import requests
   errors = requests.get(
       f'{base_url}/issues/',
       headers=headers,
       params={'limit': 5}
   ).json()
   return [{'id': e['id'], 'title': e['title']} for e in errors]
   ```

3. **Sandbox Phase**: Execute code in isolated sandbox with resource limits
4. **Response Phase**: Return structured results as JSON-RPC 2.0

### Execution Modes

1. **MCP_ONLY**: Traditional approach for compatibility
2. **CODE_EXECUTION**: Pure code execution (maximum optimization)
3. **HYBRID**: Smart routing with fallback (migration path)

## Alternatives Considered

### Alternative 1: Lazy Tool Loading

**Approach**: Load only requested tools on-demand

**Pros**:
- Partial token reduction (~90%)
- Maintains MCP compatibility
- Lower implementation risk

**Cons**:
- Still requires tool definitions
- Multiple round-trips for discovery
- Limited optimization potential
- Complex caching logic

**Decision**: Rejected - Doesn't achieve sufficient token reduction

### Alternative 2: Tool Definition Compression

**Approach**: Compress tool definitions (gzip, etc.)

**Pros**:
- Simple to implement
- Works with existing MCP
- No security concerns

**Cons**:
- Limited reduction (~50-60%)
- Decompression overhead
- Still loads unnecessary tools
- Doesn't address core issue

**Decision**: Rejected - Insufficient optimization

### Alternative 3: Server-Side Intent Resolution

**Approach**: Let MCP server handle intent → action mapping

**Pros**:
- Minimal client changes
- Server controls execution
- Centralized logic

**Cons**:
- Requires server modifications
- Not portable across services
- Doesn't reduce token usage
- Tighter coupling

**Decision**: Rejected - Doesn't solve token problem

### Alternative 4: Hybrid Approach (Selected)

**Approach**: Smart routing between MCP and code execution

**Pros**:
- Maximum token reduction (99.7%)
- Gradual migration path
- Fallback to MCP if needed
- Maintains compatibility

**Cons**:
- Requires robust sandboxing
- More complex implementation
- Security considerations
- Needs comprehensive testing

**Decision**: ✅ **Accepted** - Best balance of optimization and practicality

## Consequences

### Positive

1. **Massive Token Reduction**: 99.7% reduction in token usage
   - Traditional: ~150,000 tokens
   - Optimized: ~500 tokens
   - Savings: 149,500 tokens per operation

2. **Cost Savings**: Proportional to token reduction
   - GPT-4 input: $0.01/1K tokens → $1.50 → $0.005 (99.7% savings)
   - Claude Sonnet: $3/MTok → $0.45 → $0.0015 (99.7% savings)

3. **Latency Improvement**: 50x faster execution
   - No tool loading overhead
   - Direct execution
   - Minimal serialization

4. **Scalability**: Better resource utilization
   - Lower memory footprint
   - Higher throughput
   - Better concurrency

5. **Flexibility**: Easy to add new capabilities
   - No tool definition updates
   - Code templates are simple
   - Rapid iteration

### Negative

1. **Security Complexity**: Requires robust sandboxing
   - **Mitigation**: Multi-layer sandbox (Docker, seccomp, AppArmor)
   - **Mitigation**: Resource limits (CPU, memory, time)
   - **Mitigation**: Network isolation
   - **Mitigation**: Fail-closed design

2. **Error Handling**: More complex failure modes
   - **Mitigation**: Structured error responses
   - **Mitigation**: Comprehensive logging
   - **Mitigation**: Fallback to MCP in hybrid mode

3. **Debugging**: Harder to trace execution
   - **Mitigation**: Detailed audit logs
   - **Mitigation**: Execution replay capability
   - **Mitigation**: Debug mode with verbose output

4. **Testing**: Need comprehensive test coverage
   - **Mitigation**: Security-specific tests
   - **Mitigation**: Performance benchmarks
   - **Mitigation**: Integration tests with real services

5. **Platform Dependency**: Sandbox requires Docker/similar
   - **Mitigation**: Multiple sandbox backends (Docker, WASM, Firecracker)
   - **Mitigation**: Basic fallback for development
   - **Mitigation**: Clear documentation of requirements

### Neutral

1. **Migration Path**: Hybrid mode provides gradual transition
2. **Maintenance**: Code templates vs tool definitions (similar effort)
3. **Documentation**: Different approach requires new docs

## Implementation

### Phase 1: Core Engine (Completed)
- [x] Intent router with mode switching
- [x] Code executor with structured responses
- [x] Feature flags for gradual rollout
- [x] Hybrid mode with smart routing

### Phase 2: Security (Completed)
- [x] Docker sandbox with seccomp/AppArmor
- [x] Resource limits enforcement
- [x] Network isolation
- [x] Audit logging

### Phase 3: Production Hardening (Completed)
- [x] Metrics collection (Prometheus)
- [x] OpenTelemetry integration
- [x] Error handling and retry logic
- [x] Performance benchmarks

### Phase 4: Advanced Features (Future)
- [ ] Firecracker microVM sandbox
- [ ] WebAssembly (WASM) sandbox
- [ ] Advanced caching strategies
- [ ] Multi-tenant support

## Validation

### Performance Testing

**Benchmark Results** (see [PERFORMANCE.md](../PERFORMANCE.md)):
- Token reduction: 99.7% ✅
- Latency: 50ms avg (50x faster) ✅
- Throughput: 1000+ ops/sec ✅
- Memory: <100MB per session ✅

### Security Testing

**Security Validation** (see [SECURITY.md](../../SECURITY.md)):
- Sandbox isolation: Passed ✅
- Resource limits: Enforced ✅
- Network isolation: Verified ✅
- Privilege escalation: Blocked ✅

### Compatibility Testing

**Hybrid Mode Validation**:
- MCP fallback: Working ✅
- Smart routing: Functional ✅
- Error handling: Comprehensive ✅

## Success Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Token Reduction | >99% | 99.7% | ✅ Exceeded |
| Latency | <100ms | 50ms | ✅ Exceeded |
| Throughput | >500 ops/sec | 1000+ ops/sec | ✅ Exceeded |
| Memory | <200MB/session | <100MB | ✅ Exceeded |
| Security | No critical issues | 0 known issues | ✅ Met |

## References

- [Architecture Documentation](../ARCHITECTURE.md)
- [Performance Documentation](../PERFORMANCE.md)
- [Security Policy](../../SECURITY.md)
- [ADR-0002: Docker Sandbox](0002-docker-sandbox.md)

## Related Work

- **Model Context Protocol**: https://modelcontextprotocol.io/
- **Tool Calling Optimization**: Industry best practices for reducing token usage
- **Serverless Security**: Patterns for secure code execution
- **Container Security**: Docker, gVisor, Firecracker best practices

---

**Authors**: Ryan Hart
**Date**: 2024-11-24
**Version**: 1.0.0

"""
Basic Usage Example for MCP Optimizer Framework

This example demonstrates the simplest way to use the MCP Optimizer Framework
to execute operations with optimized token usage.
"""

import asyncio
from mcp_optimizer import CodeExecutor, FeatureFlags, ExecutionMode


async def main():
    """Basic usage example"""

    # 1. Create feature flags with default settings
    print("1. Initializing MCP Optimizer with default settings...")
    flags = FeatureFlags(
        execution_mode=ExecutionMode.HYBRID,
        enable_sandbox=True,
        enable_caching=True,
        enable_metrics=True,
    )

    # 2. Create executor instance
    print("2. Creating executor...")
    executor = CodeExecutor(flags)

    # 3. Execute a simple operation
    print("\n3. Executing 'list_errors' operation...")
    result = await executor.execute_intent(
        intent="list_errors",
        params={
            "filter": "active",
            "limit": 10
        }
    )

    # 4. Process results
    print("\n4. Results:")
    print(f"   Status: {result['result']['status']}")
    print(f"   Data: {result['result']['data']}")

    # 5. Check metadata for token usage and performance
    print("\n5. Performance Metrics:")
    metadata = result['result']['metadata']
    print(f"   Tokens used: {metadata['tokens_used']}")
    print(f"   Execution time: {metadata['execution_time_ms']:.2f}ms")
    print(f"   Cache hit: {metadata['cache_hit']}")
    print(f"   Execution mode: {metadata['mode']}")

    # 6. Execute another operation (should use cache)
    print("\n6. Executing same operation again (should hit cache)...")
    result2 = await executor.execute_intent(
        intent="list_errors",
        params={
            "filter": "active",
            "limit": 10
        }
    )

    print(f"   Cache hit: {result2['result']['metadata']['cache_hit']}")

    # 7. Execute different operation
    print("\n7. Executing 'analyze_error' operation...")
    result3 = await executor.execute_intent(
        intent="analyze_error",
        params={
            "error_id": "12345"
        }
    )

    print(f"   Status: {result3['result']['status']}")
    print(f"   Tokens used: {result3['result']['metadata']['tokens_used']}")


async def comparison_example():
    """Compare traditional MCP vs optimized approach"""

    print("\n" + "="*60)
    print("COMPARISON: Traditional MCP vs MCP Optimizer")
    print("="*60)

    # Traditional MCP simulation
    print("\nTraditional MCP:")
    print("  1. Load all tool definitions: ~150,000 tokens")
    print("  2. Parse and validate: ~2-3 seconds")
    print("  3. Execute operation: ~300 tokens")
    print("  Total: ~150,300 tokens, ~3 seconds")

    # Optimized approach
    print("\nMCP Optimizer (Hybrid Mode):")
    flags = FeatureFlags(execution_mode=ExecutionMode.HYBRID)
    executor = CodeExecutor(flags)

    import time
    start = time.time()

    result = await executor.execute_intent(
        intent="list_errors",
        params={"filter": "active", "limit": 5}
    )

    duration = (time.time() - start) * 1000  # Convert to ms
    tokens = result['result']['metadata']['tokens_used']

    print(f"  1. Progressive discovery: ~50 tokens")
    print(f"  2. Code generation: ~40 tokens")
    print(f"  3. Execute operation: ~{tokens} tokens")
    print(f"  Total: ~{tokens + 90} tokens, ~{duration:.0f}ms")

    print(f"\nToken Reduction: {((150300 - (tokens + 90)) / 150300 * 100):.1f}%")
    print(f"Speed Improvement: ~{(3000 / duration):.0f}x faster")


async def error_handling_example():
    """Demonstrate error handling"""

    print("\n" + "="*60)
    print("ERROR HANDLING EXAMPLE")
    print("="*60)

    flags = FeatureFlags()
    executor = CodeExecutor(flags)

    # Try invalid operation
    print("\n1. Testing with unknown intent (will use fallback)...")
    try:
        result = await executor.execute_intent(
            intent="unknown_operation",
            params={}
        )
        print(f"   Handled gracefully: {result['result']['status']}")
    except Exception as e:
        print(f"   Error caught: {type(e).__name__}: {e}")

    # Try operation with timeout
    print("\n2. Testing timeout scenario...")
    flags_short_timeout = FeatureFlags(max_tokens_per_request=10)
    executor_short = CodeExecutor(flags_short_timeout)

    result = await executor_short.execute_intent(
        intent="list_errors",
        params={"limit": 1000}  # Large request
    )

    if 'error' in result:
        print(f"   Error handled: {result['error']['message']}")
    else:
        print(f"   Request completed successfully")


async def metrics_example():
    """Demonstrate metrics collection"""

    print("\n" + "="*60)
    print("METRICS EXAMPLE")
    print("="*60)

    flags = FeatureFlags(enable_metrics=True)
    executor = CodeExecutor(flags)

    # Execute several operations
    print("\nExecuting 5 operations to collect metrics...")

    for i in range(5):
        await executor.execute_intent(
            intent="list_errors" if i % 2 == 0 else "analyze_error",
            params={"limit": 10} if i % 2 == 0 else {"error_id": f"err_{i}"}
        )
        print(f"  Operation {i+1} completed")

    # Get metrics summary
    summary = executor.metrics.get_summary()

    print("\nMetrics Summary:")
    print(f"  Cache hit rate: {summary['cache_hit_rate']}")
    print(f"  Total errors: {summary['total_errors']}")
    print(f"  Last tokens used: {summary['last_tokens_used']}")
    print(f"  Estimated cost: {summary['estimated_session_cost']}")
    print(f"  Active sessions: {summary['active_sessions']}")


if __name__ == "__main__":
    print("="*60)
    print("MCP OPTIMIZER FRAMEWORK - BASIC USAGE EXAMPLES")
    print("="*60)

    # Run examples
    asyncio.run(main())
    asyncio.run(comparison_example())
    asyncio.run(error_handling_example())
    asyncio.run(metrics_example())

    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
    print("\nNext steps:")
    print("  - See examples/sentry_integration.py for Sentry-specific usage")
    print("  - See examples/custom_capability.py for custom capabilities")
    print("  - Read docs/API.md for complete API reference")
    print("  - Read docs/DEPLOYMENT.md for production deployment")

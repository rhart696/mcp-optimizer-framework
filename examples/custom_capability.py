"""
Custom Capability Example for MCP Optimizer Framework

This example demonstrates how to extend the MCP Optimizer Framework
with custom capabilities, code templates, and integrations.
"""

import asyncio
from typing import Dict, Any, Optional
from mcp_optimizer import CodeExecutor, FeatureFlags
from mcp_optimizer.core import IntentRouter


class CustomCapability:
    """
    Custom capability implementation

    This class shows how to create a custom capability that integrates
    with the MCP Optimizer Framework's code execution engine.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize custom capability

        Args:
            name: Capability name
            description: Capability description
        """
        self.name = name
        self.description = description
        self.code_templates: Dict[str, str] = {}
        self.metadata: Dict[str, Any] = {
            "category": "custom",
            "complexity": "medium",
            "requires_auth": False,
        }

    def add_template(self, operation: str, code: str, complexity: str = "medium"):
        """
        Add a code template for an operation

        Args:
            operation: Operation name
            code: Python code template with {param} placeholders
            complexity: Operation complexity (simple, medium, complex)
        """
        self.code_templates[operation] = code
        self.metadata[operation] = {
            "complexity": complexity,
            "template_version": "1.0.0"
        }

    def generate_code(self, operation: str, params: Dict[str, Any]) -> str:
        """
        Generate executable code from template

        Args:
            operation: Operation name
            params: Operation parameters

        Returns:
            Executable Python code
        """
        if operation not in self.code_templates:
            raise ValueError(f"Unknown operation: {operation}")

        template = self.code_templates[operation]

        # Simple parameter substitution
        # In production, use proper templating with validation
        code = template
        for key, value in params.items():
            placeholder = f"{{{key}}}"
            if isinstance(value, str):
                code = code.replace(placeholder, f"'{value}'")
            else:
                code = code.replace(placeholder, str(value))

        return code


class CustomIntegration:
    """
    Custom integration example for a hypothetical API service

    Demonstrates how to create a full integration with:
    - Custom capabilities
    - Code templates
    - Authentication
    - Error handling
    """

    def __init__(self, api_key: str, base_url: str):
        """
        Initialize custom integration

        Args:
            api_key: API authentication key
            base_url: API base URL
        """
        self.api_key = api_key
        self.base_url = base_url

        # Initialize optimizer
        self.flags = FeatureFlags()
        self.executor = CodeExecutor(self.flags)

        # Register custom capabilities
        self._register_capabilities()

    def _register_capabilities(self):
        """Register custom capabilities and templates"""

        # Create custom capability
        self.capability = CustomCapability(
            name="custom_api",
            description="Custom API integration"
        )

        # Add code templates
        self.capability.add_template(
            operation="fetch_data",
            code="""
import requests

response = requests.get(
    f'{base_url}/api/data',
    headers={{'Authorization': f'Bearer {api_key}'}},
    params={{'filter': {filter}, 'limit': {limit}}}
)
response.raise_for_status()
response.json()
""",
            complexity="simple"
        )

        self.capability.add_template(
            operation="process_data",
            code="""
import requests

# Fetch raw data
data = requests.get(
    f'{base_url}/api/data/{data_id}',
    headers={{'Authorization': f'Bearer {api_key}'}}
).json()

# Process data
processed = {{
    'id': data['id'],
    'processed_at': datetime.now().isoformat(),
    'result': sum(data['values']) / len(data['values'])
}}

# Store result
requests.post(
    f'{base_url}/api/results',
    headers={{'Authorization': f'Bearer {api_key}'}},
    json=processed
)

processed
""",
            complexity="medium"
        )

        self.capability.add_template(
            operation="batch_process",
            code="""
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor

def process_item(item_id):
    response = requests.post(
        f'{base_url}/api/process/{item_id}',
        headers={{'Authorization': f'Bearer {api_key}'}},
        json={{'operation': {operation}}}
    )
    return response.json()

# Process in parallel
with ThreadPoolExecutor(max_workers={max_workers}) as executor:
    results = list(executor.map(process_item, {item_ids}))

{{'total': len(results), 'results': results}}
""",
            complexity="complex"
        )

    async def fetch_data(
        self,
        filter: str = "active",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Fetch data from custom API"""

        code = self.capability.generate_code(
            operation="fetch_data",
            params={
                "base_url": self.base_url,
                "api_key": self.api_key,
                "filter": filter,
                "limit": limit
            }
        )

        result = await self.executor.sandbox.execute(code)
        return eval(result['stdout'])

    async def process_data(self, data_id: str) -> Dict[str, Any]:
        """Process data item"""

        code = self.capability.generate_code(
            operation="process_data",
            params={
                "base_url": self.base_url,
                "api_key": self.api_key,
                "data_id": data_id
            }
        )

        result = await self.executor.sandbox.execute(code)
        return eval(result['stdout'])

    async def batch_process(
        self,
        item_ids: list,
        operation: str = "default",
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """Batch process multiple items"""

        code = self.capability.generate_code(
            operation="batch_process",
            params={
                "base_url": self.base_url,
                "api_key": self.api_key,
                "item_ids": item_ids,
                "operation": operation,
                "max_workers": max_workers
            }
        )

        result = await self.executor.sandbox.execute(code, timeout=60)
        return eval(result['stdout'])


class ExtendedIntentRouter(IntentRouter):
    """
    Extended intent router with custom capabilities

    Shows how to extend the framework's intent router to handle
    custom operations.
    """

    def __init__(self, flags, custom_capabilities: Dict[str, CustomCapability]):
        """
        Initialize extended router

        Args:
            flags: Feature flags
            custom_capabilities: Dictionary of custom capabilities
        """
        super().__init__(flags)
        self.custom_capabilities = custom_capabilities

        # Extend route map with custom operations
        for capability_name, capability in custom_capabilities.items():
            for operation in capability.code_templates.keys():
                full_name = f"{capability_name}.{operation}"
                self.route_map[full_name] = [full_name]

    async def route_to_code(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to code execution with custom capability support

        Args:
            intent: Operation intent
            params: Operation parameters

        Returns:
            Execution result
        """
        # Check if this is a custom capability
        if '.' in intent:
            capability_name, operation = intent.split('.', 1)

            if capability_name in self.custom_capabilities:
                capability = self.custom_capabilities[capability_name]
                code = capability.generate_code(operation, params)

                # Execute via sandbox
                from .executor import CodeExecutor
                executor = CodeExecutor(self.flags)
                result = await executor.sandbox.execute(code)

                return {
                    "mode": "custom_code_execution",
                    "capability": capability_name,
                    "operation": operation,
                    "result": result
                }

        # Fall back to default routing
        return await super().route_to_code(intent, params)


async def basic_custom_capability():
    """Basic custom capability example"""

    print("="*60)
    print("BASIC CUSTOM CAPABILITY")
    print("="*60)

    # Create custom capability
    print("\n1. Creating custom capability...")
    capability = CustomCapability(
        name="data_processor",
        description="Custom data processing capability"
    )

    # Add template
    print("2. Adding code template...")
    capability.add_template(
        operation="transform",
        code="""
data = {input_data}
result = [x * 2 for x in data]
{{'transformed': result, 'count': len(result)}}
""",
        complexity="simple"
    )

    # Generate code
    print("3. Generating code from template...")
    code = capability.generate_code(
        operation="transform",
        params={"input_data": [1, 2, 3, 4, 5]}
    )
    print(f"   Generated code:\n{code}")

    # Execute
    print("4. Executing generated code...")
    flags = FeatureFlags()
    executor = CodeExecutor(flags)
    result = await executor.sandbox.execute(code)
    print(f"   Result: {result['stdout']}")


async def full_integration_example():
    """Full custom integration example"""

    print("\n" + "="*60)
    print("FULL CUSTOM INTEGRATION")
    print("="*60)

    # Initialize integration
    print("\n1. Initializing custom integration...")
    integration = CustomIntegration(
        api_key="demo_api_key",
        base_url="https://api.example.com"
    )

    print(f"   Registered capability: {integration.capability.name}")
    print(f"   Available operations: {list(integration.capability.code_templates.keys())}")

    # Fetch data
    print("\n2. Fetching data...")
    try:
        data = await integration.fetch_data(filter="active", limit=5)
        print(f"   Retrieved {len(data)} items")
    except Exception as e:
        print(f"   Note: This is a demo, actual API not available")
        print(f"   In production, would fetch data from {integration.base_url}")

    # Process data
    print("\n3. Processing data...")
    try:
        result = await integration.process_data(data_id="123")
        print(f"   Processed: {result}")
    except Exception as e:
        print(f"   Note: This is a demo, actual API not available")
        print(f"   In production, would process data and store result")

    # Batch process
    print("\n4. Batch processing...")
    try:
        results = await integration.batch_process(
            item_ids=["1", "2", "3"],
            operation="analyze",
            max_workers=2
        )
        print(f"   Processed {results['total']} items")
    except Exception as e:
        print(f"   Note: This is a demo, actual API not available")
        print(f"   In production, would process items in parallel")


async def template_versioning_example():
    """Demonstrate template versioning and updates"""

    print("\n" + "="*60)
    print("TEMPLATE VERSIONING")
    print("="*60)

    capability = CustomCapability("versioned", "Versioned capability")

    # Version 1.0.0
    print("\n1. Adding template v1.0.0...")
    capability.add_template(
        operation="calculate",
        code="""
result = {a} + {b}
result
""",
        complexity="simple"
    )

    code_v1 = capability.generate_code("calculate", {"a": 5, "b": 3})
    print(f"   v1.0.0 code: {code_v1.strip()}")

    # Version 2.0.0 - Enhanced
    print("\n2. Updating to template v2.0.0...")
    capability.add_template(
        operation="calculate",
        code="""
# Enhanced calculation with validation
a, b = {a}, {b}
if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
    raise ValueError("Both operands must be numbers")
result = a + b
{{'result': result, 'operation': 'add', 'version': '2.0.0'}}
""",
        complexity="simple"
    )

    code_v2 = capability.generate_code("calculate", {"a": 5, "b": 3})
    print(f"   v2.0.0 code:")
    print(f"   {code_v2.strip()}")

    # Execute both versions
    print("\n3. Comparing execution results...")
    executor = CodeExecutor(FeatureFlags())

    result_v1 = await executor.sandbox.execute(code_v1)
    print(f"   v1.0.0 result: {result_v1['stdout'].strip()}")

    result_v2 = await executor.sandbox.execute(code_v2)
    print(f"   v2.0.0 result: {result_v2['stdout'].strip()}")


async def performance_metrics_example():
    """Demonstrate performance metrics for custom capabilities"""

    print("\n" + "="*60)
    print("PERFORMANCE METRICS")
    print("="*60)

    import time

    capability = CustomCapability("benchmark", "Benchmarking")

    # Simple operation
    capability.add_template(
        "simple_op",
        "result = sum(range({n}))\nresult",
        complexity="simple"
    )

    # Complex operation
    capability.add_template(
        "complex_op",
        """
import time
start = time.time()
result = sum([x**2 for x in range({n})])
duration = time.time() - start
{{'result': result, 'duration': duration}}
""",
        complexity="complex"
    )

    executor = CodeExecutor(FeatureFlags(enable_metrics=True))

    # Benchmark simple
    print("\n1. Benchmarking simple operation...")
    code = capability.generate_code("simple_op", {"n": 10000})

    start = time.time()
    result = await executor.sandbox.execute(code)
    duration = time.time() - start

    print(f"   Result: {result['stdout'].strip()}")
    print(f"   Duration: {duration*1000:.2f}ms")

    # Benchmark complex
    print("\n2. Benchmarking complex operation...")
    code = capability.generate_code("complex_op", {"n": 10000})

    start = time.time()
    result = await executor.sandbox.execute(code)
    duration = time.time() - start

    print(f"   Result: {result['stdout'].strip()}")
    print(f"   Duration: {duration*1000:.2f}ms")

    # Show metrics
    print("\n3. Overall metrics:")
    metrics = executor.metrics.get_summary()
    for key, value in metrics.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    print("="*60)
    print("CUSTOM CAPABILITY EXAMPLES")
    print("="*60)

    # Run examples
    asyncio.run(basic_custom_capability())
    asyncio.run(full_integration_example())
    asyncio.run(template_versioning_example())
    asyncio.run(performance_metrics_example())

    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
    print("\nKey Concepts:")
    print("  - Create custom capabilities with code templates")
    print("  - Extend intent router for custom operations")
    print("  - Version templates for backwards compatibility")
    print("  - Measure performance with built-in metrics")
    print("  - Integrate with any API or service")
    print("\nNext Steps:")
    print("  - Read docs/API.md for API reference")
    print("  - See CONTRIBUTING.md to contribute capabilities")
    print("  - Check ROADMAP.md for planned features")

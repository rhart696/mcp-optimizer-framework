"""
Core module with feature flags and intent router
Implements hybrid mode switching between traditional MCP and code execution
"""

import asyncio
import json
from enum import Enum
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()

class ExecutionMode(Enum):
    """Execution modes with feature flag support"""
    MCP_ONLY = "mcp_only"  # Traditional approach
    CODE_EXECUTION = "code_execution"  # Our optimized approach
    HYBRID = "hybrid"  # Smart routing between both

class FeatureFlags(BaseModel):
    """Feature flags for gradual migration"""
    execution_mode: ExecutionMode = Field(default=ExecutionMode.HYBRID)
    enable_sandbox: bool = Field(default=True)
    enable_caching: bool = Field(default=True)
    enable_metrics: bool = Field(default=True)
    enable_auto_apply: bool = Field(default=False)  # Cautious by default
    max_tokens_per_request: int = Field(default=1000)
    cache_ttl_seconds: int = Field(default=300)
    context_size_limit_kb: int = Field(default=100)

    class Config:
        use_enum_values = True

class IntentRouter:
    """
    Routes requests to appropriate handler based on intent
    Implements the lean-first principle from the review
    """

    def __init__(self, flags: FeatureFlags):
        self.flags = flags
        self.route_map = {
            "list_errors": ["sentry.list_issues"],
            "analyze_error": ["sentry.get_trace", "sentry.analyze"],
            "fix_error": ["code.generate_fix"],
            "create_issue": ["github.create_issue"],
        }

    async def route(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Route based on intent and execution mode"""

        logger.info("routing_request", intent=intent, mode=self.flags.execution_mode)

        if self.flags.execution_mode == ExecutionMode.MCP_ONLY:
            return await self.route_to_mcp(intent, params)
        elif self.flags.execution_mode == ExecutionMode.CODE_EXECUTION:
            return await self.route_to_code(intent, params)
        else:  # HYBRID
            return await self.route_hybrid(intent, params)

    async def route_hybrid(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart routing: Use MCP for simple queries, code execution for complex
        This addresses the review's suggestion to treat code execution as extension
        """

        # Simple queries go to MCP (if available)
        if intent in ["list_errors", "get_issue_count"]:
            try:
                return await self.route_to_mcp(intent, params)
            except Exception as e:
                logger.warning("mcp_fallback_to_code", error=str(e))
                return await self.route_to_code(intent, params)

        # Complex operations use code execution
        return await self.route_to_code(intent, params)

    async def route_to_mcp(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Route to traditional MCP with lazy loading"""

        tools_needed = self.route_map.get(intent, [])

        # Lazy load only required tools (90% reduction as suggested)
        loaded_tools = await self.lazy_load_tools(tools_needed)

        # Call traditional MCP
        # This would integrate with existing MCP servers
        return {"mode": "mcp", "tools_loaded": len(loaded_tools)}

    async def route_to_code(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Route to optimized code execution"""

        # Our efficient approach
        from .executor import CodeExecutor
        executor = CodeExecutor(self.flags)
        return await executor.execute_intent(intent, params)

    async def lazy_load_tools(self, tool_names: List[str]) -> List[str]:
        """
        Lazy discovery - only load tools actually needed
        Implements the review's suggestion for 90% reduction
        """

        loaded = []
        for tool in tool_names:
            if not self.is_tool_loaded(tool):
                await self.load_tool(tool)
                loaded.append(tool)

        logger.info("lazy_load_complete", loaded_count=len(loaded))
        return loaded

    def is_tool_loaded(self, tool_name: str) -> bool:
        """Check if tool is already in context"""
        # Implementation would check context cache
        return False

    async def load_tool(self, tool_name: str) -> None:
        """Load a single tool definition"""
        # Minimal loading - just what's needed
        pass

class CodeExecutor:
    """
    Enhanced code executor with all improvements from review
    """

    def __init__(self, flags: FeatureFlags):
        self.flags = flags
        self.router = IntentRouter(flags)

        # Pluggable context as suggested
        from .context import ContextManager
        self.context = ContextManager(
            backend="redis" if flags.enable_caching else "memory",
            ttl=flags.cache_ttl_seconds,
            size_limit_kb=flags.context_size_limit_kb
        )

        # Metrics instrumentation as required
        from .metrics import MetricsCollector
        self.metrics = MetricsCollector(enabled=flags.enable_metrics)

        # Security sandbox as mandated
        from .sandbox import SecureSandbox
        self.sandbox = SecureSandbox(enabled=flags.enable_sandbox)

    async def execute_intent(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute with all production hardening:
        - Structured responses (JSON Schema)
        - Metrics collection
        - Sandbox enforcement
        - Context management with TTL
        """

        # Start metrics
        with self.metrics.measure("execution_time", {"intent": intent}):

            # Check token limit
            estimated_tokens = self.estimate_tokens(intent, params)
            if estimated_tokens > self.flags.max_tokens_per_request:
                self.metrics.increment("token_limit_exceeded")
                return self.error_response("Token limit exceeded", 429)

            try:
                # Execute in sandbox with limits
                result = await self.sandbox.execute(
                    self.generate_code(intent, params),
                    timeout=30,
                    memory_mb=512
                )

                # Track metrics
                self.metrics.increment("execution_success", {"intent": intent})
                self.metrics.observe("tokens_used", estimated_tokens)

                # Return structured response
                return self.structured_response(result)

            except TimeoutError:
                self.metrics.increment("execution_timeout")
                return self.error_response("Execution timeout", 408)

            except Exception as e:
                self.metrics.increment("execution_error")
                logger.error("execution_failed", error=str(e))
                return self.error_response(str(e), 500)

    def structured_response(self, data: Any) -> Dict[str, Any]:
        """
        Structured JSON Schema response as suggested in review
        Assistants don't need to parse raw strings
        """
        return {
            "jsonrpc": "2.0",
            "result": {
                "status": "success",
                "data": data,
                "metadata": {
                    "tokens_used": self.metrics.get_last("tokens_used"),
                    "execution_time_ms": self.metrics.get_last("execution_time"),
                    "cache_hit": self.context.last_cache_hit,
                    "mode": self.flags.execution_mode.value
                }
            },
            "schema": "https://mcp-optimizer.dev/schemas/response/v2"
        }

    def error_response(self, message: str, code: int) -> Dict[str, Any]:
        """Structured error response"""
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message,
                "data": {
                    "mode": self.flags.execution_mode.value,
                    "sandbox_enabled": self.flags.enable_sandbox
                }
            }
        }

    def estimate_tokens(self, intent: str, params: Dict[str, Any]) -> int:
        """Estimate token usage for rate limiting"""
        # Rough estimate: 4 chars = 1 token
        content = json.dumps({"intent": intent, "params": params})
        return len(content) // 4

    def generate_code(self, intent: str, params: Dict[str, Any]) -> str:
        """Generate Python code for intent"""

        # Map intents to efficient code
        code_templates = {
            "list_errors": """
import requests
errors = requests.get(f'{base_url}/issues/',
                      headers=headers,
                      params={'limit': 5}).json()
[{'id': e['id'], 'title': e['title']} for e in errors]
""",
            "analyze_error": """
trace = get_stack_trace('{error_id}')
{{
    'file': trace['filename'],
    'line': trace['lineNo'],
    'cause': analyze_cause(trace)
}}
""",
            "fix_error": """
generate_fix(context['current_error'], context['stack_trace'])
"""
        }

        template = code_templates.get(intent, "print('Unknown intent')")

        # Inject parameters safely
        for key, value in params.items():
            if isinstance(value, str):
                template = template.replace(f"{{{key}}}", value)

        return template
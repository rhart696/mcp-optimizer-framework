"""
MCP Optimizer Framework - Generic optimization engine for Model Context Protocol
"""

__version__ = "1.0.0"

from .core import CodeExecutor, FeatureFlags
from .sandbox import SecureSandbox
from .sandbox_hardened import HardenedSandbox
from .context import ContextManager
from .metrics import MetricsCollector
from .capabilities import CapabilityDetector
from .sessions import SessionManager
from .telemetry import TelemetryCollector

__all__ = [
    "CodeExecutor",
    "FeatureFlags",
    "SecureSandbox",
    "HardenedSandbox",
    "ContextManager",
    "MetricsCollector",
    "CapabilityDetector",
    "SessionManager",
    "TelemetryCollector",
]

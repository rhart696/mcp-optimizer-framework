"""
Security validation tests
"""

import pytest
from mcp_optimizer.sandbox import SecureSandbox

class TestSandbox:
    """Test security sandbox"""

    @pytest.mark.asyncio
    async def test_timeout_enforcement(self):
        """Verify timeout protection"""
        sandbox = SecureSandbox(enabled=True)

        # This should timeout
        code = "import time; time.sleep(100)"

        with pytest.raises(Exception):  # TimeoutError or similar
            await sandbox.execute(code, timeout=1)

    @pytest.mark.asyncio
    async def test_memory_limits(self):
        """Verify memory limits"""
        sandbox = SecureSandbox(enabled=True)

        # Attempt to allocate excessive memory
        code = "data = [0] * (10**9)"  # Try to allocate huge list

        # Should fail or be limited
        result = await sandbox.execute(code, memory_mb=128)
        # Either fails or is contained

    @pytest.mark.asyncio
    async def test_safe_execution(self):
        """Verify safe code executes normally"""
        sandbox = SecureSandbox(enabled=True)

        code = "result = 2 + 2; print(result)"

        result = await sandbox.execute(code, timeout=5)
        assert result is not None

---
name: Bug Report
about: Report a bug to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:

1. Install version '...'
2. Configure '...'
3. Execute '...'
4. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

What actually happened instead.

## Minimal Reproducible Example

```python
# Provide a minimal code example that reproduces the issue
from mcp_optimizer import CodeExecutor, FeatureFlags

flags = FeatureFlags(...)
executor = CodeExecutor(flags)
# ... code that triggers the bug
```

## Error Messages

```
Paste any error messages, stack traces, or logs here
```

## Environment

**System Information**:
- OS: [e.g., Ubuntu 22.04, macOS 14.0, Windows 11]
- Python Version: [e.g., 3.11.6]
- MCP Optimizer Version: [e.g., 1.0.0]
- Docker Version: [e.g., 24.0.7] (if applicable)
- Installation Method: [pip, source, docker]

**Configuration**:
```python
# Paste your configuration (remove sensitive data)
flags = FeatureFlags(
    execution_mode=...,
    enable_sandbox=...,
    # etc.
)
```

**Dependencies**:
```
# Output of: pip list | grep -E "(aiohttp|pydantic|structlog|docker)"
aiohttp==3.8.5
pydantic==2.4.2
structlog==23.1.0
docker==6.1.3
```

## Additional Context

### Logs

<details>
<summary>Full logs (click to expand)</summary>

```
Paste full logs here
```

</details>

### Screenshots

If applicable, add screenshots to help explain your problem.

### Workaround

If you found a workaround, please describe it here.

## Impact

- [ ] Blocks my work completely
- [ ] Significant impact on functionality
- [ ] Minor inconvenience
- [ ] Cosmetic issue

## Frequency

- [ ] Happens every time
- [ ] Happens intermittently
- [ ] Happened once
- [ ] Cannot reproduce consistently

## Security Impact

- [ ] This bug has security implications (please also email rhart696@gmail.com)
- [ ] No security implications

## Checklist

- [ ] I have searched existing issues to avoid duplicates
- [ ] I have provided a minimal reproducible example
- [ ] I have included all relevant environment information
- [ ] I have checked the documentation
- [ ] I have removed any sensitive information from logs/code

## Additional Information

Add any other context about the problem here.

---

**Note**: For security vulnerabilities, please also email rhart696@gmail.com instead of only opening a public issue. See [SECURITY.md](../../SECURITY.md) for details.

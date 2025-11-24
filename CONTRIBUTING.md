# Contributing to MCP Optimizer Framework

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the MCP Optimizer Framework.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Commit Message Conventions](#commit-message-conventions)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to rhart696@gmail.com.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a branch for your changes
5. Make your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip or pipenv for package management
- Docker (optional, for sandbox testing)
- Redis (optional, for session management testing)
- Git

### Local Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/mcp-optimizer-framework.git
cd mcp-optimizer-framework

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Verify installation
pytest tests/
```

### Optional Components

```bash
# Install Docker for sandbox testing
# See https://docs.docker.com/get-docker/

# Start Redis for session management
docker run -d -p 6379:6379 redis:7-alpine

# Verify Docker sandbox
docker --version
python -c "import docker; print(docker.from_env().ping())"
```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Write code following our code standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests locally**
   ```bash
   pytest tests/
   black mcp_optimizer/ tests/
   flake8 mcp_optimizer/ tests/
   mypy mcp_optimizer/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a pull request** on GitHub

## Code Standards

We follow strict code quality standards to maintain a professional, production-ready codebase.

### Python Style

- **Black** for code formatting (line length: 100)
- **Flake8** for linting
- **isort** for import sorting
- **mypy** for type checking (strongly encouraged)

```bash
# Format code
black mcp_optimizer/ tests/

# Sort imports
isort mcp_optimizer/ tests/

# Lint
flake8 mcp_optimizer/ tests/

# Type check
mypy mcp_optimizer/
```

### Code Quality Guidelines

1. **Type Hints**: Use type hints for all function signatures
   ```python
   def process_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
       pass
   ```

2. **Docstrings**: All public functions and classes must have docstrings
   ```python
   def execute_code(code: str, timeout: int = 30) -> Dict[str, Any]:
       """
       Execute code in a secure sandbox.

       Args:
           code: Python code to execute
           timeout: Maximum execution time in seconds

       Returns:
           Dictionary with stdout, stderr, and exit_code

       Raises:
           TimeoutError: If execution exceeds timeout
           RuntimeError: If sandbox execution fails
       """
       pass
   ```

3. **Error Handling**: Use specific exception types and provide context
   ```python
   try:
       result = await sandbox.execute(code)
   except TimeoutError as e:
       logger.error("execution_timeout", error=str(e))
       raise
   except Exception as e:
       logger.error("execution_failed", error=str(e))
       raise RuntimeError(f"Sandbox execution failed: {e}")
   ```

4. **Logging**: Use structlog for structured logging
   ```python
   logger.info("operation_started", intent=intent, mode=mode)
   logger.error("operation_failed", error=str(e), context=ctx)
   ```

5. **Security**: Follow security best practices
   - Never execute untrusted code without sandboxing
   - Validate all inputs
   - Use parameterized queries
   - Sanitize user-provided strings
   - Apply principle of least privilege

## Testing Requirements

All contributions must include appropriate tests.

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **Security Tests**: Test sandbox isolation and limits
4. **Performance Tests**: Verify performance claims

### Writing Tests

```python
import pytest
from mcp_optimizer import CodeExecutor, FeatureFlags

class TestCodeExecutor:
    """Test code executor functionality"""

    @pytest.mark.asyncio
    async def test_execute_simple_code(self):
        """Test basic code execution"""
        executor = CodeExecutor(FeatureFlags())
        result = await executor.execute_intent("test", {})
        assert result is not None
        assert "jsonrpc" in result

    def test_token_estimation(self):
        """Test token estimation accuracy"""
        executor = CodeExecutor(FeatureFlags())
        tokens = executor.estimate_tokens("test", {"key": "value"})
        assert tokens > 0
        assert tokens < 100
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=mcp_optimizer --cov-report=html tests/

# Run specific test file
pytest tests/test_core.py

# Run specific test
pytest tests/test_core.py::TestCodeExecutor::test_execute_simple_code

# Run only security tests
pytest tests/test_security.py

# Run benchmarks
pytest tests/test_benchmarks.py -v
```

### Coverage Requirements

- Minimum 80% coverage for new code
- 90%+ coverage target for critical components (sandbox, security)
- All public APIs must have tests

## Pull Request Process

1. **Before submitting**:
   - Ensure all tests pass
   - Run code formatters (black, isort)
   - Run linters (flake8, mypy)
   - Update documentation
   - Add entry to CHANGELOG.md under `[Unreleased]`

2. **PR Description**:
   - Clear title describing the change
   - Reference related issues (#123)
   - Describe what changed and why
   - Include screenshots for UI changes
   - Note breaking changes

3. **Review Process**:
   - At least one maintainer approval required
   - All CI checks must pass
   - Address review feedback promptly
   - Keep PR scope focused

4. **After Approval**:
   - Maintainer will merge using "Squash and merge"
   - PR will be closed automatically
   - Branch will be deleted

## Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependency updates
- **ci**: CI/CD changes

### Examples

```bash
# New feature
git commit -m "feat(sandbox): add WASM backend support"

# Bug fix
git commit -m "fix(metrics): correct token counting logic"

# Documentation
git commit -m "docs(readme): add Docker installation instructions"

# Breaking change
git commit -m "feat(api): change execute_intent signature

BREAKING CHANGE: execute_intent now requires timeout parameter"
```

## Issue Guidelines

### Bug Reports

Use the bug report template and include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Docker version)
- Relevant logs or error messages
- Minimal reproducible example

### Feature Requests

Use the feature request template and include:
- Clear description of the feature
- Use cases and motivation
- Proposed API or implementation (optional)
- Alternatives considered
- Additional context

### Questions

For questions:
- Check existing documentation first
- Search closed issues
- Use GitHub Discussions for general questions
- Use issues for specific technical questions

## Development Tips

### Running Individual Components

```bash
# Test sandbox isolation
python -m mcp_optimizer.sandbox

# Test metrics collection
python -m mcp_optimizer.metrics

# Run CLI
mcp-optimizer --help
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
pytest tests/test_core.py -v -s

# Run with debugger
pytest tests/test_core.py --pdb
```

### Docker Development

```bash
# Build custom test image
docker build -t mcp-optimizer-test -f Dockerfile.test .

# Run tests in Docker
docker run --rm mcp-optimizer-test pytest
```

## Getting Help

- **Documentation**: Check the `docs/` directory
- **GitHub Issues**: Search existing issues
- **GitHub Discussions**: Ask questions, share ideas
- **Email**: rhart696@gmail.com for security issues

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in documentation

Thank you for contributing to MCP Optimizer Framework!

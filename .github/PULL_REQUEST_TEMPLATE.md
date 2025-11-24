# Pull Request

## Description

### Summary

Provide a clear and concise description of what this PR does.

### Related Issues

Closes #(issue number)
Relates to #(issue number)
Depends on #(PR number)

## Type of Change

Select the type of change:

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Documentation update
- [ ] CI/CD changes
- [ ] Dependencies update
- [ ] Security fix

## Motivation and Context

Why is this change required? What problem does it solve?

## Changes Made

List the main changes in this PR:

-
-
-

## Testing

### Test Coverage

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Security tests added/updated
- [ ] Performance benchmarks added/updated
- [ ] All tests passing locally

### Test Results

```bash
# Paste test output here
pytest tests/ -v
```

**Coverage**: XX% (goal: >80%)

### Manual Testing

Describe any manual testing performed:

1.
2.
3.

### Test Environment

- OS: [e.g., Ubuntu 22.04]
- Python Version: [e.g., 3.11.6]
- Docker Version: [e.g., 24.0.7]

## Performance Impact

### Benchmarks

If this PR affects performance, include benchmark results:

**Before**:
```
Metric: XXXms
Throughput: XXX ops/sec
Memory: XXX MB
```

**After**:
```
Metric: XXXms
Throughput: XXX ops/sec
Memory: XXX MB
```

**Impact**: [+X% improvement / -Y% regression / No significant change]

### Token Usage Impact

If applicable:
- Token reduction: [+X% / No change]
- Token overhead: [+X tokens / No change]

## Security Considerations

- [ ] No security implications
- [ ] Security review required
- [ ] Security tests added
- [ ] Follows security best practices
- [ ] No secrets exposed in code/commits

**Security Notes**: [Any security-related considerations]

## Breaking Changes

- [ ] This PR introduces breaking changes

If yes, describe the breaking changes and migration path:

### What breaks:
-

### Migration guide:
```python
# Before
old_api_usage()

# After
new_api_usage()
```

### Deprecation timeline:
- Deprecated in: vX.Y.Z
- Removed in: vX.Y.Z

## Documentation

- [ ] Code comments added/updated
- [ ] Docstrings added/updated
- [ ] README.md updated
- [ ] CHANGELOG.md updated
- [ ] Architecture docs updated (if applicable)
- [ ] ADR added (for significant decisions)
- [ ] API documentation updated
- [ ] Migration guide created (if breaking change)

## Code Quality

### Checklist

- [ ] Code follows project style guidelines (black, flake8)
- [ ] Self-review of code completed
- [ ] Code is self-documenting and commented where needed
- [ ] Type hints added for new functions
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate and structured
- [ ] No debug prints or commented code left behind
- [ ] No TODO comments without associated issues

### Code Review

- [ ] Ready for review
- [ ] Work in progress (Draft PR)

## Dependencies

### New Dependencies

List any new dependencies added:

- `package-name==version` - [reason for addition]

### Updated Dependencies

- `package-name`: old-version → new-version - [reason for update]

## Deployment Notes

### Configuration Changes

Are there any configuration changes required?

```python
# New configuration
flags = FeatureFlags(
    new_option=value  # Description
)
```

### Environment Variables

New environment variables:
- `ENV_VAR_NAME`: [description]

### Infrastructure Changes

- [ ] Database migrations required
- [ ] Infrastructure changes required
- [ ] Requires Docker image rebuild
- [ ] Requires service restart

### Rollback Plan

How to rollback if this causes issues:

1.
2.

## Backward Compatibility

- [ ] Fully backward compatible
- [ ] Deprecated features (list below)
- [ ] Breaking changes (described above)

## Additional Notes

### Screenshots/Videos

If applicable, add screenshots or videos demonstrating the change.

### Metrics to Monitor

After deployment, monitor:

-
-
-

### Follow-up Tasks

Issues or tasks to address in future PRs:

- [ ] #(issue) - Description
- [ ] #(issue) - Description

## Checklist

### Before Requesting Review

- [ ] I have read [CONTRIBUTING.md](../CONTRIBUTING.md)
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

### Commit Messages

- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] No merge commits (rebased on latest main)

### Final Check

- [ ] PR title is clear and descriptive
- [ ] PR description is complete
- [ ] Labels are added appropriately
- [ ] Assignees are set
- [ ] Milestone is set (if applicable)
- [ ] Draft status is correct

## Reviewer Notes

### Areas to Focus On

Please pay special attention to:

-
-

### Questions for Reviewers

-
-

---

## For Maintainers

### Review Checklist

- [ ] Code quality meets standards
- [ ] Tests are comprehensive
- [ ] Documentation is clear
- [ ] No security concerns
- [ ] Performance is acceptable
- [ ] Breaking changes are justified

### Merge Strategy

- [ ] Squash and merge
- [ ] Rebase and merge
- [ ] Merge commit

**Merge after**: [number] approvals

---

Thank you for contributing to MCP Optimizer Framework! 🚀

---
trigger: model_decision
description: Apply when making git commits or writing commit messages
---

# Conventional Commits

Use conventional commit format:

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

**Types:**
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Formatting (no code change)
- **refactor**: Code restructuring
- **test**: Adding/modifying tests
- **chore**: Maintenance tasks
- **perf**: Performance improvements
- **ci**: CI/CD changes

**Examples:**
- `feat(validator): add JSON-LD export support`
- `fix(material): correct percentage validation logic`
- `docs(readme): add installation instructions`
- `test(dpp): add unit tests for passport validation`

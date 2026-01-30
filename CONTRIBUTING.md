# Contributing to dppvalidator

Thank you for your interest in contributing to **dppvalidator**! This document
provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) for package management

### Quick Start

```bash
# Clone the repository
git clone https://github.com/artiso-ai/dppvalidator.git
cd dppvalidator

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check src tests
uv run ruff format --check src tests
```

## Development Workflow

We follow **gitflow** for branching:

1. Create a feature branch from `develop`:

   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

1. Make your changes, following the code style guidelines below.

1. Run tests and linting:

   ```bash
   uv run pytest
   uv run ruff check src tests --fix
   uv run ruff format src tests
   ```

1. Commit with conventional commit messages:

   ```bash
   git commit -m "feat: add new validation rule for X"
   ```

1. Push and create a Pull Request to `develop`.

## Code Style

### Python Guidelines

- **Type hints**: All public APIs must have type hints
- **Docstrings**: Use Google-style docstrings for public functions
- **Line length**: 100 characters max
- **Formatting**: Use `ruff format`
- **Linting**: Use `ruff check`

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Examples:

```
feat: add credentialStatus field to passport model
fix: handle network errors in schema loader
docs: update API reference for ValidationEngine
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/dppvalidator --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_validators.py

# Run tests matching pattern
uv run pytest -k "async"
```

### Test Requirements

- Maintain **90%+ code coverage**
- Add tests for all new features
- Include unit tests in `tests/unit/`
- Include integration tests in `tests/integration/` for end-to-end flows

## Pull Request Process

1. Ensure all tests pass and coverage is maintained
1. Update documentation if needed
1. Add entry to `CHANGELOG.md` under "Unreleased"
1. Request review from maintainers
1. Address review feedback
1. Squash and merge once approved

## Reporting Issues

### Bug Reports

Please include:

- Python version
- dppvalidator version
- Minimal reproducible example
- Expected vs actual behavior
- Full error traceback

### Feature Requests

Please describe:

- Use case and motivation
- Proposed API or behavior
- Any relevant UNTP/ESPR specifications

## Code of Conduct

Be respectful and constructive. We're building tools to support sustainable
product transparency - let's work together positively.

## Questions?

- Open a [GitHub Discussion](https://github.com/artiso-ai/dppvalidator/discussions)
- Check existing [Issues](https://github.com/artiso-ai/dppvalidator/issues)

Thank you for contributing! 🌱

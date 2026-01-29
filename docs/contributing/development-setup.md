# Development Setup

Set up your development environment for contributing to dppvalidator.

## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git

## Clone the Repository

```
git clone https://github.com/artiso-ai/dppvalidator.git
cd dppvalidator
```

## Install Dependencies

### Using uv (recommended)

```
# Install all dependencies including dev tools
uv sync

# Activate the virtual environment
source .venv/bin/activate
```

### Using pip

```
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Verify Installation

```
# Run tests
uv run pytest

# Check linting
uv run ruff check .

# Type check
uv run ty check src/
```

## Project Structure

```text
dppvalidator/
├── src/dppvalidator/      # Main package
│   ├── models/            # Pydantic models
│   ├── validators/        # Validation logic
│   ├── exporters/         # Export formats
│   ├── cli/               # Command line interface
│   └── plugins/           # Plugin system
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── property/          # Property-based tests
│   └── fuzz/              # Fuzzing tests
├── docs/                  # Documentation
└── benchmarks/            # Performance benchmarks
```

## Development Workflow

1. Create a feature branch from `develop`
1. Make your changes
1. Run tests and linting
1. Submit a pull request

```
# Create feature branch
git checkout develop
git checkout -b feature/my-feature

# Make changes...

# Run checks
uv run ruff check .
uv run pytest

# Commit and push
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature
```

## Pre-commit Hooks

Install pre-commit hooks for automatic linting:

```
uv run pre-commit install
```

## Next Steps

- [Code Style](code-style.md) — Coding conventions
- [Testing](testing.md) — Writing tests

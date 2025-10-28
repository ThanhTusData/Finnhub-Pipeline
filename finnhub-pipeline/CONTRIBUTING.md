# Contributing Guidelines

Thank you for your interest in contributing to the Finnhub Trading Pipeline!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Run tests
6. Submit a pull request

## Development Setup

```bash
# Clone repository
git clone https://github.com/your-username/finnhub-pipeline.git
cd finnhub-pipeline

# Create environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run before committing:
```bash
make lint
```

## Testing

```bash
# Run all tests
make test

# Run specific tests
pytest finnhub_producer/tests/test_validation.py
pytest spark_processor/tests/test_transformations.py

# With coverage
pytest --cov=src --cov-report=html
```

## Pull Request Process

1. Update documentation for any changed functionality
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

## Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `chore:` Build/tooling changes

Example:
```
feat: add support for crypto symbols

- Add crypto symbol validation
- Update producer configuration
- Add crypto-specific tests
```

## Issue Reporting

When reporting issues, include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Logs/screenshots if applicable

## Questions?

Open an issue or reach out to maintainers.
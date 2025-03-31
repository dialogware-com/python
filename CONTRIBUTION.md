# Contributing to DialogWare

Thank you for your interest in contributing to DialogWare! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful, inclusive, and considerate in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your feature or bugfix
5. Make your changes
6. Submit a pull request

## Development Environment

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/python.git dialogware-python
cd dialogware-python

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Coding Standards

We follow PEP 8 style guidelines for Python code. Additionally:

- Use type hints where appropriate
- Write docstrings for all functions, classes, and modules
- Keep functions focused and small
- Use meaningful variable and function names
- Comment complex code sections

### Code Structure

- Place new features in appropriate modules under `src/dialogware/`
- For plugins, use the plugin system in `src/dialogware/plugins/`

## Pull Request Process

1. Ensure your code follows our coding standards
2. Update documentation if necessary
3. Add or update tests as appropriate
4. Make sure all tests pass
5. Submit a pull request with a clear description of the changes and any relevant issue numbers

### Commit Messages

Follow these guidelines for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

## Testing

- Write unit tests for new functionality
- Ensure all tests pass before submitting a pull request
- Run tests using pytest:

```bash
pytest
```

## Documentation

- Update the README.md if you change functionality
- Document new features with examples
- Update docstrings for modified functions
- Consider adding to the wiki for complex features

## Community

- Join our [Discord server](https://discord.gg/dialogware) for discussions
- Report bugs and request features through GitHub issues
- Subscribe to our newsletter for updates

## Plugin Development

If you're developing a new plugin for DialogWare:

1. Create a new directory under `src/dialogware/plugins/`
2. Implement the required interfaces (see existing plugins for examples)
3. Add appropriate tests in the `tests/` directory
4. Document your plugin's functionality and usage

Thank you for contributing to DialogWare!



1. Instalacja podstawowa:
```bash
pip install -r requirements.txt
```

2. Instalacja dla deweloperów:
```bash
pip install -r requirements-dev.txt
```

3. Uruchomienie testów:
```bash
tox
```

4. Instalacja pre-commit hooków:
```bash
pre-commit install
```

5. Sprawdzenie formatowania:
```bash
black .
flake8 .
mypy src/mdirtree
isort .
```

Aktualizacja
```bash
pip install -e .
```


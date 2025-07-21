# Homepy Agent Guidelines

## Build/Test Commands
- Build: `poetry build`
- Install dependencies: `poetry install`
- Install test dependencies: `poetry install --extras test`
- Run CLI: `poetry run homepy` or `python -m homepy`
- Test: `poetry run pytest tests/` or `./run_tests.sh`

## Code Style
- Python 3.12+ required
- Use Poetry for dependency management
- Always use type hints: `def func(param: str) -> None:`
- Import order: stdlib, third-party, local (abc, typing, rich, homepy)
- Use pathlib.Path for file operations, not os.path
- Class naming: PascalCase (HomeResource, SymlinkResource)
- Method/variable naming: snake_case
- Use descriptive docstrings for classes and complex methods
- Error handling: Check file existence before operations
- Use rich library for progress tracking and output formatting
- Abstract base classes should use @abstractmethod decorator
- Prefer explicit type annotations over implicit Any
- Use Path objects consistently for file system operations
- Print informative messages for user feedback during operations
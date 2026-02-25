# GitHub Copilot Instructions - Python Development Standards

## Testing Standards
- **Framework**: Always use `pytest` for generating and running tests.
- **Execution**: When providing commands to run tests, always include the `--reuse-db` flag to optimize performance.
- **Style**: Prefer functional tests and fixtures over class-based unit tests where appropriate.

## Code Style & Quality
- **Type Hinting**: Always use explicit Type Hinting for all Python function signatures (parameters and return types).
- **Complexity**: Maintain a maximum cognitive complexity of 10.
- **Return Statements**: Use a maximum of **4 return statements** per function. If more are needed, refactor the logic.
- **PEP 8**: Follow PEP 8 guidelines strictly.
- **Line Length**: The maximum allowed line length is 120 characters.
- **Style**: Follow single responsibility principle.

## Documentation
- **Format**: Always use **Google-style** docstrings for all new functions, classes, and modules.
- **Structure**:
    - Include a concise summary line.
    - Include an `Args:` section (with types and descriptions).
    - Include a `Returns:` section (with type and description).
    - Include a `Raises:` section if the code explicitly raises an exception.

## Agent Documentation Files
- **Location**: All AI agent-generated summary, implementation, and refactoring documentation files must be placed in the `agent_docs/` folder.
- **Examples**: Implementation summaries, refactoring reports, verification documents, improvement notes, etc.
- **Naming**: Use descriptive names with dates (e.g., `implementation_user_deactivation_2026-02-24.md`, `refactoring_complexity_reduction_2026-02-24.md`).
- **Purpose**: Keep project root clean and organize all agent-generated documentation in one location.
- **Exception**: User-facing documentation (README, installation guides, etc.) should remain in appropriate locations (`docs/`, project root, etc.).

## Example Reference
```python
def validate_and_score(value: int, limit: int) -> str:
    """
    Checks a value against a limit and returns a category string.

    Args:
        value (int): The score to be evaluated.
        limit (int): The threshold for passing.

    Returns:
        str: A string indicating the status ('invalid', 'fail', 'pass', or 'high-pass').
    """
    if value < 0:
        return "invalid"  # Return 1

    if value < limit:
        return "fail"     # Return 2

    if value > limit * 2:
        return "high-pass" # Return 3

    return "pass"          # Return 4

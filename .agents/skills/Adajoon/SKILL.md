```markdown
# Adajoon Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the Adajoon Python codebase. It covers file naming, import/export styles, commit message patterns, and testing approaches, providing a foundation for contributing effectively to the project.

## Coding Conventions

### File Naming
- Use **camelCase** for file names.
  - Example: `dataProcessor.py`, `userProfile.py`

### Import Style
- Use **relative imports** within the codebase.
  - Example:
    ```python
    from .utils import parseData
    from ..models import User
    ```

### Export Style
- Use **named exports** (explicitly listing what is exported).
  - Example:
    ```python
    __all__ = ['parseData', 'User']
    ```

### Commit Message Patterns
- Commit types are mixed, with prefixes like `cursor` and `feat`.
- Keep commit messages concise (average 43 characters).
  - Example:
    ```
    feat: add user authentication logic
    cursor: fix pagination bug in results
    ```

## Workflows

*No automated workflows detected in this repository. All tasks are performed manually via standard development practices.*

## Testing Patterns

- **Testing Framework:** Unknown (not detected).
- **Test File Pattern:** Test files follow the `*.test.ts` naming convention, suggesting TypeScript-based tests, possibly for a frontend or API layer.
  - Example: `userService.test.ts`
- **How to Write Tests:** Place test files alongside or within a `tests/` directory, using the `.test.ts` suffix.

## Commands

| Command | Purpose |
|---------|---------|
| /commit-convention | Show commit message guidelines |
| /file-naming | Show file naming conventions |
| /import-style | Show import/export examples |
| /testing-patterns | Show how to write and locate tests |
```
